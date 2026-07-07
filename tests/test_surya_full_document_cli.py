from __future__ import annotations

from pathlib import Path

from PIL import Image

from court_ocr_extract.ocr_backends.base import OCRBackendStatus
from court_ocr_extract.ocr_backends.surya_ocr import SuryaOCRBackend
from court_ocr_extract.settings import PipelineSettings


def test_surya_ocr_images_empty_marker_does_not_truncate_or_break(tmp_path, monkeypatch) -> None:
    image_paths = [tmp_path / "page_001.png", tmp_path / "page_002.png"]
    for image_path in image_paths:
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
        lambda paths: [
            {
                "text_lines": [
                    {
                        "text": "phan dau NỘI DUNG VỤ ÁN phan sau",
                        "bbox": [20, 20, 260, 40],
                        "confidence": 0.97,
                    }
                ]
            },
            {
                "text_lines": [
                    {
                        "text": "trang hai van duoc xu ly",
                        "bbox": [20, 20, 260, 40],
                        "confidence": 0.96,
                    }
                ]
            },
        ],
    )

    result = backend.ocr_images(
        image_paths,
        stop_marker="",
        debug_visual=True,
        work_dir=tmp_path / "case_full_document_synthetic",
    )

    assert result.backend == "surya"
    assert result.status == "success"
    assert result.marker_found is False
    assert result.pages_processed == 2
    assert "NỘI DUNG VỤ ÁN" in result.text
    assert "phan sau" in result.text
    assert "trang hai van duoc xu ly" in result.text
    assert "Marker not found before max page limit." not in result.warnings
    assert (tmp_path / "case_full_document_synthetic" / "ocr_surya" / "page_002_lines.json").exists()


def test_surya_backend_source_does_not_fallback_to_tesseract_paddle_or_cloud() -> None:
    source_path = Path(__file__).parents[1] / "src" / "court_ocr_extract" / "ocr_backends" / "surya_ocr.py"
    source = source_path.read_text(encoding="utf-8").lower()

    assert "tesseract" not in source
    assert "paddle" not in source
    assert "google" not in source
    assert "openai" not in source
    assert "gemini" not in source
    assert "cloud" not in source
