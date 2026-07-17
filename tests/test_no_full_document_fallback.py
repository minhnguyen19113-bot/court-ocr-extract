from __future__ import annotations

import pytest

from court_ocr_extract.decision_tail import scan_decision_tail
from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult


def test_decision_tail_guard_never_expands_to_full_document() -> None:
    calls: list[list[int]] = []

    def fake_ocr_batch(page_numbers: list[int]) -> OCRResult:
        calls.append(page_numbers)
        return OCRResult(
            backend="synthetic",
            status="success",
            pages_processed=len(page_numbers),
            marker_found=False,
            marker_page=None,
            text="",
            pages=[
                OCRPage(
                    page_index=page,
                    lines=[{"line_id": f"p{page:03d}_l0001", "text": "Synthetic tail"}],
                )
                for page in page_numbers
            ],
        )

    record = scan_decision_tail(
        case_id="synthetic_case",
        source_index=1,
        pdf_hash=None,
        backend="synthetic",
        pages_total=20,
        ocr_batch=fake_ocr_batch,
        batch_size=2,
        max_scan_pages=4,
    )

    assert calls == [[19, 20], [17, 18]]
    assert record.status == "heading_not_found"
    assert record.scanned_page_numbers == [17, 18, 19, 20]
    assert "decision_heading_not_found_within_scan_limit" in record.warnings


def test_decision_tail_guard_rejects_an_unbounded_scan_limit() -> None:
    with pytest.raises(ValueError, match="full-document fallback is disabled"):
        scan_decision_tail(
            case_id="synthetic_case",
            source_index=1,
            pdf_hash="synthetic_hash",
            backend="synthetic",
            pages_total=20,
            ocr_batch=lambda _page_numbers: OCRResult(
                backend="synthetic",
                status="success",
                pages_processed=0,
                pages=[],
            ),
            batch_size=4,
            max_scan_pages=None,
        )


def test_heading_not_found_leaves_relationship_blank_with_short_note() -> None:
    row = build_final_excel_rows(
        {
            "case_id": "synthetic_case",
            "document_type": "judgment_criminal_first_instance",
            "metadata": {},
            "trial_panel": {},
            "decision_tail_status": "heading_not_found",
            "defendants": [
                {"entity_id": "defendant_001", "full_name": "Person Synthetic Alpha"}
            ],
        }
    )[0]

    assert row["QUAN HỆ PHÁP LUẬT"] == ""
    assert (
        "Không tìm thấy phần Quyết định trong phạm vi OCR cuối văn bản"
        in row["GHI CHÚ"]
    )
