from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_judgment_and_acceptance_fields_map_independently() -> None:
    row = build_final_excel_rows(_result())[0]

    assert row["SỐ BẢN ÁN"] == "901/2099/HS-ST"
    assert row["NGÀY TUYÊN ÁN (DD/MM/YYYY)"] == "01/02/2099"
    assert row["SỐ THỤ LÝ"] == "701/2099/TLST-HS"
    assert row["NGÀY THỤ LÝ (DD/MM/YYYY)"] == "03/04/2099"


def test_missing_case_fields_do_not_cross_fallback() -> None:
    result = _result()
    result["metadata"].pop("judgment_number")
    result["metadata"].pop("case_acceptance_date")
    result["metadata"]["trial_date"] = "05/06/2099"

    row = build_final_excel_rows(result)[0]

    assert row["SỐ BẢN ÁN"] == ""
    assert row["NGÀY THỤ LÝ (DD/MM/YYYY)"] == ""
    assert "Thiếu số bản án" in row["GHI CHÚ"]
    assert "Thiếu ngày thụ lý" in row["GHI CHÚ"]


def _result() -> dict:
    charge = "Charge Synthetic Alpha"
    return {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {
            "source_region": FRONT_PRE_CONTENT,
            "judgment_number": "901/2099/HS-ST",
            "judgment_date": "1/2/2099",
            "case_acceptance_number": "701/2099/TLST-HS",
            "case_acceptance_date": "3/4/2099",
        },
        "trial_panel": {
            "source_region": FRONT_PRE_CONTENT,
            "presiding_judge": "Judge Synthetic",
        },
        "defendants": [
            {
                "entity_id": "defendant_alpha",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Person Synthetic Alpha",
                "birth_date_or_year": "1990",
                "current_address": "Zone Synthetic Alpha",
            }
        ],
        "case_charges": [charge],
        "defendant_charge_map": {"defendant_alpha": [charge]},
        "charge_output": {
            "charge_evidence": [
                {"charge": charge, "source_region": DECISION_TAIL}
            ]
        },
    }
