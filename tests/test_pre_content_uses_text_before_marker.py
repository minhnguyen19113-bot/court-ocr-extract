from __future__ import annotations

from types import SimpleNamespace

from court_ocr_extract import extraction_pipeline
from court_ocr_extract.ocr_backends.base import OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord


def test_extraction_prefers_cached_text_before_marker(monkeypatch) -> None:
    captured: list[str] = []
    extractor = SimpleNamespace(
        check_available=lambda: SimpleNamespace(available=True, reason="synthetic"),
        extract_from_text=lambda text, case_id: captured.append(text)
        or {"case": {}, "participants": [], "document_warnings": []},
    )
    monkeypatch.setattr(extraction_pipeline, "get_extractor_backend", lambda name: extractor)
    monkeypatch.setattr(extraction_pipeline, "track", lambda values, *args, **kwargs: values)
    result = OCRResult(
        backend="surya",
        status="success",
        pages_processed=1,
        marker_found=True,
        marker_page=1,
        text="full OCR text should not be used",
        metadata={"text_before_marker": "synthetic pre-content only"},
    )

    extraction_pipeline.extract_from_ocr_cache_records(
        [OCRCacheRecord("case_001_synthetic", 1, None, result)],
        extractor_name="synthetic",
    )

    assert captured == ["synthetic pre-content only"]

