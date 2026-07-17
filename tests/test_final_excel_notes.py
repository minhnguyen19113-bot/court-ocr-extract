from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows


def test_missing_values_are_blank_and_explained_without_json() -> None:
    result = {
        "document_type": "unknown",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            {
                "full_name": "Người Synthetic Thiếu Dữ Liệu",
                "raw_block": "Địa chỉ nhà số 123456789 tại Vùng Synthetic",
                "evidence_line_ids": ["p001_l0007"],
                "needs_review": True,
                "warnings": ["field_too_long:occupation"],
            }
        ],
        "warnings": ["ocr_low_confidence"],
    }

    row = build_final_excel_rows(result)[0]
    notes = row["GHI CHÚ"]

    assert row["LOẠI ÁN"] == ""
    assert row["CCCD"] == ""
    assert row["NĂM SINH"] == ""
    assert row["ĐỊA CHỈ"] == ""
    assert "Thiếu CCCD/CMND" in notes
    assert "Thiếu năm sinh" in notes
    assert "Thiếu địa chỉ" in notes
    assert "Thiếu ngày thụ lý" in notes
    assert "Không xác định chắc quan hệ pháp luật" in notes
    assert "OCR nghi ngờ" in notes
    assert "Field bị validator loại" in notes
    assert "Người cần review" in notes
    assert "evidence=p001_l0007" in notes
    assert "{" not in notes and "[" not in notes


def test_criminal_case_leaves_relationship_blank_with_charge_note() -> None:
    result = {
        "document_type": "judgment_criminal_first_instance",
        "metadata": {
            "case_acceptance_number": "999/2099/TLST-HS",
            "case_acceptance_date": "09/04/2099",
        },
        "trial_panel": {"presiding_judge": "Chủ Tọa Synthetic"},
        "defendants": [
            {
                "full_name": "Người Synthetic C",
                "birth_date_or_year": "1999",
                "cccd": "000000000",
                "current_address": "Vùng Synthetic C",
            }
        ],
    }

    row = build_final_excel_rows(result)[0]

    assert row["QUAN HỆ PHÁP LUẬT"] == ""
    assert "Chưa gắn chắc tội danh với bị cáo từ phần Quyết định" in row["GHI CHÚ"]
