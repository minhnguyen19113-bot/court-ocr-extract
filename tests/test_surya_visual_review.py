from __future__ import annotations

from PIL import Image

from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult
from court_ocr_extract.ocr_backends.surya_ocr import write_surya_page_artifacts
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.review_html import write_ocr_review


def test_surya_visual_review_links_overlay_json_and_text(tmp_path) -> None:
    image_path = tmp_path / "page.png"
    Image.new("RGB", (320, 220), "white").save(image_path)
    lines = [
        {
            "line_id": "p001_l0001",
            "page_number": 1,
            "text": "dong review",
            "bbox": [20.0, 20.0, 220.0, 40.0],
            "confidence": 0.91,
            "reading_order": 1,
            "warnings": [],
        }
    ]
    artifact = write_surya_page_artifacts(
        tmp_path / "ocr_surya",
        image_path=image_path,
        page_number=1,
        lines=lines,
        page_text="dong review",
        warnings=[],
    )
    record = OCRCacheRecord(
        case_id="case_001_synthetic",
        source_index=1,
        pdf_hash="synthetic",
        result=OCRResult(
            backend="surya",
            status="success",
            pages_processed=1,
            marker_found=False,
            marker_page=None,
            text="dong review",
            pages=[
                OCRPage(
                    page_index=1,
                    text="dong review",
                    image_path=artifact["original_image_path"],
                    lines=lines,
                    blocks=[artifact],
                )
            ],
        ),
    )

    review_path = write_ocr_review(tmp_path / "ocr_surya" / "review.html", [record], base_dir=tmp_path / "ocr_surya")
    html = review_path.read_text(encoding="utf-8")

    assert "case_001_synthetic" in html
    assert "page_001_bbox.png" in html
    assert "page_001_lines.json" in html
    assert "page_001_text.md" in html
    assert "p001_l0001" in html
    assert "dong review" in html
