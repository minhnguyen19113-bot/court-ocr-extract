from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from tests.test_rule_anchor_metadata import _extract


def test_acceptance_date_is_blocked_when_number_token_is_missing() -> None:
    output = _extract(
        [
            "Bản án số: 907/2099/HS-ST",
            "thụ lý số ngày 03 tháng 2 năm 2099; xét xử ngày 20 tháng 2 năm 2099",
            "Đối với bị cáo:",
            "Người Synthetic A, sinh năm 1990",
        ]
    )

    assert output["metadata"]["case_acceptance_number"] is None
    assert output["metadata"]["case_acceptance_date"] is None
    assert "acceptance_date_blocked_missing_acceptance_number" in output["warnings"]


def test_final_builder_does_not_use_unbound_acceptance_date() -> None:
    rows = build_final_excel_rows(
        {
            "case_id": "synthetic_case",
            "document_type": "judgment_criminal_first_instance",
            "metadata": {"case_acceptance_date": "03/02/2099"},
            "trial_panel": {},
            "defendants": [
                {"full_name": "Người Synthetic A", "birth_date_or_year": "1990"}
            ],
        }
    )

    assert rows[0]["SỐ THỤ LÝ"] == ""
    assert rows[0]["NGÀY THỤ LÝ (DD/MM/YYYY)"] == ""
