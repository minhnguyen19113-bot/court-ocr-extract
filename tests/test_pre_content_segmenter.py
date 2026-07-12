from __future__ import annotations

from court_ocr_extract.extractors.pre_content_segmenter import route_document, segment_pre_content
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult


def test_segments_before_ocr_tolerant_heading_and_preserves_evidence() -> None:
    result = _result([
        (1, "BẢN ÁN SỐ: 01/2026/HS-ST"),
        (1, "NHÂN DANH NƯỚC CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"),
        (1, "Bị cáo: Nguyễn A"),
        (1, "NOI DUNG VU AN:"),
        (1, "Dòng nội dung không được lấy"),
    ])

    segment = segment_pre_content(result)

    assert segment["document_type"] == "judgment_criminal_first_instance"
    assert segment["stop_line_id"] == "p001_l0004"
    assert "Dòng nội dung" not in segment["pre_content_text"]
    assert segment["pre_content_lines"][0]["line_id"] == "p001_l0001"


def test_missing_heading_uses_first_three_pages_and_warns() -> None:
    result = _result([(page, f"Trang {page}") for page in range(1, 5)])

    segment = segment_pre_content(result, max_fallback_pages=3)

    assert segment["end_page"] == 3
    assert "Trang 4" not in segment["pre_content_text"]
    assert "pre_content_stop_heading_not_found_using_page_limit" in segment["warnings"]


def test_document_router_detects_correction_notice_and_unknown() -> None:
    correction = route_document("THÔNG BÁO\nSỬA CHỮA BỔ SUNG BẢN ÁN")
    unknown = route_document("Tài liệu tổng hợp không có anchor")

    assert correction["document_type"] == "correction_notice"
    assert unknown["document_type"] == "unknown"
    assert unknown["needs_review"] is True


def _result(rows):
    pages = {}
    for page_number, text in rows:
        page_lines = pages.setdefault(page_number, [])
        page_lines.append({"line_id": f"p{page_number:03d}_l{len(page_lines) + 1:04d}", "page_number": page_number, "text": text})
    return OCRResult(
        backend="synthetic", status="success", pages_processed=len(pages), marker_found=False,
        marker_page=None, text="\n".join(text for _, text in rows),
        pages=[OCRPage(page_index=page, text="", lines=lines) for page, lines in sorted(pages.items())],
    )
