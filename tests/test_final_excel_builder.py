from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.final_excel_schema import FINAL_EXCEL_COLUMNS


def test_builder_maps_common_fields_and_one_row_per_person() -> None:
    result = {
        "document_type": "judgment_criminal_first_instance",
        "metadata": {
            "judgment_number": "01/2099/HS-ST",
            "case_acceptance_number": "999/2099/TLST-HS",
            "legal_relationship": "Tội danh synthetic",
        },
        "trial_panel": {"presiding_judge": "Chủ Tọa Synthetic"},
        "anchor_segments": {
            "metadata_lines": [
                {
                    "line_id": "p001_l0002",
                    "text": "thụ lý số 999/2099/TLST-HS ngày 09 tháng 4 năm 2099",
                }
            ]
        },
        "defendants": [
            {
                "full_name": "Người Synthetic A",
                "birth_date_or_year": "03/3/2010",
                "cccd": "000000000000",
                "current_address": "hiện tại: Vùng Synthetic A",
            }
        ],
        "participants": [
            {
                "role": "Bị hại",
                "full_name": "Người Synthetic B",
                "birth_date_or_year": "ngày 20 tháng 12 năm 1997",
                "raw_block": "CCCD số 0000000000",
                "address": "Vùng Synthetic B",
            }
        ],
        "warnings": [],
    }

    rows = build_final_excel_rows(result)

    assert len(rows) == 2
    assert all(list(row) == FINAL_EXCEL_COLUMNS for row in rows)
    assert all(row["LOẠI ÁN"] == "Hình sự sơ thẩm" for row in rows)
    assert all(row["SỐ THỤ LÝ"] == "999/2099/TLST-HS" for row in rows)
    assert all(row["NGÀY THỤ LÝ (DD/MM/YYYY)"] == "09/04/2099" for row in rows)
    assert all(row["HỌ TÊN CHỦ TỌA"] == "Chủ Tọa Synthetic" for row in rows)
    assert rows[0]["TƯ CÁCH TỐ TỤNG"] == "Bị cáo"
    assert rows[1]["TƯ CÁCH TỐ TỤNG"] == "Bị hại"
    assert [row["NĂM SINH"] for row in rows] == ["2010", "1997"]
    assert [row["CCCD"] for row in rows] == ["000000000000", "0000000000"]
    assert rows[0]["ĐỊA CHỈ"] == "Vùng Synthetic A"
