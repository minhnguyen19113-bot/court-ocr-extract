from __future__ import annotations

from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord, read_ocr_cache_record, write_ocr_cache_record
from court_ocr_extract.review_html import write_ocr_review


def test_marker_and_early_stop_metadata_round_trip(tmp_path) -> None:
    result = OCRResult(
        backend="surya",
        status="success",
        pages_processed=3,
        marker_found=True,
        marker_page=3,
        text="synthetic pre-content",
        metadata={
            "marker": {
                "found": True,
                "confidence": "high",
                "page_number": 3,
                "line_index": 1,
                "matched_text": "NỘI DUNG VỤ ÁN",
                "normalized_match": "noi dung vu an",
                "source": "filtered_lines",
                "before_text": "synthetic pre-content",
                "context": "synthetic",
            },
            "early_stop": {
                "enabled": True,
                "triggered": True,
                "stopped_after_page": 3,
                "pages_skipped_after_marker": 7,
                "reason": "marker_found",
            },
            "pages_total": 10,
            "text_before_marker": "synthetic pre-content",
        },
    )
    path = write_ocr_cache_record(OCRCacheRecord("case_001_synthetic", 1, None, result), tmp_path)

    restored = read_ocr_cache_record(path)

    assert restored.result.metadata["marker"]["confidence"] == "high"
    assert restored.result.metadata["early_stop"]["pages_skipped_after_marker"] == 7
    assert restored.result.metadata["text_before_marker"] == "synthetic pre-content"


def test_debug_html_contains_marker_and_early_stop_summary(tmp_path) -> None:
    result = OCRResult(
        backend="surya",
        status="success",
        pages_processed=2,
        marker_found=True,
        marker_page=2,
        text="synthetic pre-content",
        pages=[
            OCRPage(page_index=2, lines=[{"text": "NỘI DUNG VỤ ÁN", "marker_match": True}])
        ],
        metadata={
            "marker": {
                "found": True,
                "confidence": "high",
                "matched_text": "NỘI DUNG VỤ ÁN",
            },
            "early_stop": {
                "triggered": True,
                "pages_skipped_after_marker": 8,
                "reason": "marker_found",
            },
            "pages_total": 10,
        },
    )

    path = write_ocr_review(
        tmp_path / "review.html",
        [OCRCacheRecord("case_001_synthetic", 1, None, result)],
        base_dir=tmp_path,
    )
    html = path.read_text(encoding="utf-8")

    assert "Marker found" in html
    assert "Early stop triggered" in html
    assert "2 / 10" in html
    assert "<mark>" in html
