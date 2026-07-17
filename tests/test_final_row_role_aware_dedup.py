from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows


def test_dedup_uses_case_name_and_normalized_role() -> None:
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            {"full_name": "Người Synthetic A"},
        ],
        "participants": [
            {"role": "Bị hại", "full_name": "Người Synthetic A"},
            {"role": "Bị hại", "full_name": "Người Synthetic A"},
            {
                "role": "Người có quyền và nghĩa vụ liên quan",
                "full_name": "Người Synthetic A",
            },
        ],
    }

    rows = build_final_excel_rows(result)

    assert len(rows) == 2
    assert [row["TƯ CÁCH TỐ TỤNG"] for row in rows] == [
        "Bị cáo",
        "Bị hại",
    ]
