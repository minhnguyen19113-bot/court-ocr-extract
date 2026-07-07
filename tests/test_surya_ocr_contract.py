from __future__ import annotations

import importlib
import json

from PIL import Image

from court_ocr_extract.ocr_backends.base import OCRBackendStatus
from court_ocr_extract.ocr_backends.surya_ocr import SuryaOCRBackend, normalize_surya_prediction
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
