from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from court_ocr_extract.ocr_backends.base import OCRBackendStatus
from court_ocr_extract.ocr_backends.surya_ocr import (
    SuryaAPIDetection,
    SuryaOCRBackend,
    _unsupported_surya_api_message,
    normalize_surya_prediction,
)
from court_ocr_extract.settings import PipelineSettings


def test_surya_check_available_reports_install_hint_when_missing(monkeypatch) -> None:
    real_import_module = importlib.import_module

    def fake_import_module(name: str, *args, **kwargs):
        if name == "surya":
            raise ModuleNotFoundError("synthetic missing surya")
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr("court_ocr_extract.ocr_backends.surya_ocr.importlib.import_module", fake_import_module)

    status = SuryaOCRBackend(PipelineSettings()).check_available()

    assert status.name == "surya"
    assert status.available is False
    assert 'pip install -e ".[ocr]"' in status.reason
    assert "pip install surya-ocr" in status.reason


def test_normalize_surya_prediction_sorts_lines_and_preserves_schema() -> None:
    warnings: list[str] = []

    lines = normalize_surya_prediction(
        {
            "text_lines": [
                {"text": "dong thu hai", "bbox": [20, 80, 220, 100], "confidence": 0.77},
                {"text": "dong thu nhat", "bbox": [20, 20, 220, 40], "confidence": None},
            ]
        },
        page_number=1,
        warnings=warnings,
    )

    assert [line["text"] for line in lines] == ["dong thu nhat", "dong thu hai"]
    assert lines[0]["line_id"] == "p001_l0001"
    assert lines[0]["bbox"] == [20.0, 20.0, 220.0, 40.0]
    assert lines[0]["confidence"] is None
    assert lines[1]["confidence"] == 0.77
    assert lines[0]["reading_order"] == 1
    assert "reading_order_fallback_used" in warnings


def test_surya_prediction_uses_reading_order_before_combined_text() -> None:
    lines = normalize_surya_prediction(
        {
            "blocks": [
                {
                    "html": "<p>dong thu hai</p>",
                    "polygon": [[20, 80], [220, 80], [220, 100], [20, 100]],
                    "confidence": 0.77,
                    "reading_order": 2,
                },
                {
                    "html": "<p>dong thu nhat</p>",
                    "polygon": [[20, 20], [220, 20], [220, 40], [20, 40]],
                    "confidence": 0.99,
                    "reading_order": 1,
                },
            ]
        },
        page_number=1,
    )

    assert [line["text"] for line in lines] == ["dong thu nhat", "dong thu hai"]
    assert lines[0]["bbox"] == [20.0, 20.0, 220.0, 40.0]
    assert lines[0]["reading_order"] == 1
    assert lines[1]["reading_order"] == 2


def test_surya_backend_mocked_output_creates_ocr_result_and_artifacts(tmp_path, monkeypatch) -> None:
    image_path = tmp_path / "page_001.png"
    Image.new("RGB", (320, 220), "white").save(image_path)

    backend = SuryaOCRBackend(PipelineSettings())
    monkeypatch.setattr(
        backend,
        "check_available",
        lambda: OCRBackendStatus("surya", True, "synthetic available"),
    )
    monkeypatch.setattr(
        backend,
        "_run_surya_on_images",
        lambda image_paths: [
            {
                "text_lines": [
                    {"text": "dong thu hai", "bbox": [20, 80, 220, 100], "confidence": 0.42},
                    {"text": "dong thu nhat", "bbox": [20, 20, 220, 40], "confidence": 0.98},
                ]
            }
        ],
    )

    result = backend.ocr_images(
        [image_path],
        stop_marker="NOI DUNG VU AN",
        debug_visual=True,
        work_dir=tmp_path / "case_001_synthetic",
    )

    artifacts_dir = tmp_path / "case_001_synthetic" / "ocr_surya"
    lines_json = artifacts_dir / "page_001_lines.json"

    assert result.backend == "surya"
    assert result.pages_processed == 1
    assert result.pages[0].lines[0]["line_id"] == "p001_l0001"
    assert result.text == "dong thu nhat\ndong thu hai"
    assert (artifacts_dir / "page_001_original.png").exists()
    assert (artifacts_dir / "page_001_bbox.png").exists()
    assert lines_json.exists()
    assert (artifacts_dir / "page_001_text.md").exists()
    assert (artifacts_dir / "combined_text.md").exists()
    assert (artifacts_dir / "manifest.json").exists()
    assert (artifacts_dir / "index.html").exists()
    assert json.loads(lines_json.read_text(encoding="utf-8"))[0]["text"] == "dong thu nhat"


def test_surya_ocr_pdf_prefix_uses_rendered_pages_and_creates_artifacts(tmp_path, monkeypatch) -> None:
    import court_ocr_extract.ocr_backends.surya_ocr as surya_ocr

    rendered_image = tmp_path / "rendered_page_001.png"
    Image.new("RGB", (320, 220), "white").save(rendered_image)
    synthetic_pdf = tmp_path / "synthetic_contract.pdf"

    def fake_render_pdf_pages(pdf_path, output_dir, dpi, max_pages):
        assert pdf_path == synthetic_pdf
        assert max_pages == 1
        output_dir.mkdir(parents=True, exist_ok=True)
        return [SimpleNamespace(image_path=rendered_image, page_number=1)]

    backend = SuryaOCRBackend(PipelineSettings())
    monkeypatch.setattr(
        backend,
        "check_available",
        lambda: OCRBackendStatus("surya", True, "synthetic available"),
    )
    monkeypatch.setattr(surya_ocr, "render_pdf_pages", fake_render_pdf_pages)
    monkeypatch.setattr(
        backend,
        "_run_surya_on_images",
        lambda image_paths: [
            {
                "blocks": [
                    {
                        "html": "<p>dong thu hai</p>",
                        "polygon": [[20, 80], [220, 80], [220, 100], [20, 100]],
                        "confidence": 0.42,
                        "reading_order": 2,
                    },
                    {
                        "html": "<p>dong thu nhat</p>",
                        "polygon": [[20, 20], [220, 20], [220, 40], [20, 40]],
                        "confidence": None,
                        "reading_order": 1,
                    },
                ]
            }
        ],
    )

    result = backend.ocr_pdf_prefix(
        synthetic_pdf,
        max_pages=1,
        stop_marker="NOI DUNG VU AN",
        debug_visual=True,
        work_dir=tmp_path / "case_ocr_pdf_prefix_synthetic",
    )

    artifacts_dir = tmp_path / "case_ocr_pdf_prefix_synthetic" / "ocr_surya"
    lines = json.loads((artifacts_dir / "page_001_lines.json").read_text(encoding="utf-8"))

    assert result.backend == "surya"
    assert result.pages_processed == 1
    assert result.text == "dong thu nhat\ndong thu hai"
    assert result.pages[0].text == "dong thu nhat\ndong thu hai"
    assert result.pages[0].lines[0]["line_id"] == "p001_l0001"
    assert result.pages[0].lines[0]["bbox"] == [20.0, 20.0, 220.0, 40.0]
    assert result.pages[0].lines[0]["confidence"] is None
    assert lines[1]["confidence"] == 0.42
    assert (artifacts_dir / "page_001_original.png").exists()
    assert (artifacts_dir / "page_001_bbox.png").exists()
    assert (artifacts_dir / "page_001_text.md").read_text(encoding="utf-8") == result.text
    assert (artifacts_dir / "manifest.json").exists()


def test_surya_backend_source_has_no_placeholder_or_tesseract_fallback() -> None:
    source_path = Path(__file__).parents[1] / "src" / "court_ocr_extract" / "ocr_backends" / "surya_ocr.py"
    source = source_path.read_text(encoding="utf-8").lower()

    assert "runtime wiring is incomplete" not in source
    assert "surya ocr runtime wiring" not in source
    assert "tesseract" not in source
    assert "paddle" not in source


def test_unsupported_surya_api_message_is_explicit() -> None:
    message = _unsupported_surya_api_message(
        SuryaAPIDetection(
            kind="unsupported",
            version="9.9.9",
            details="surya-ocr version 9.9.9; fake incompatible signature",
        )
    )

    assert "Surya package is installed but this adapter does not support the installed API." in message
    assert "Detected surya-ocr version 9.9.9" in message
