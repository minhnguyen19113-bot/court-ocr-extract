from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_non_defendant_primary_role_receives_case_level_charges() -> None:
    charges = ["Charge Synthetic A", "Charge Synthetic B"]
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "participants": [
            {
                "role": "Bị hại",
                "full_name": "Person Synthetic Victim",
                "source_region": FRONT_PRE_CONTENT,
            }
        ],
        "case_charges": charges,
        "charge_output": {
            "case_charges": charges,
            "defendant_charge_map": {},
            "charge_evidence": [
                {
                    "charge": charge,
                    "source_region": DECISION_TAIL,
                    "line_ids": [f"p010_l{index:04d}"],
                }
                for index, charge in enumerate(charges, start=1)
            ],
            "warnings": [],
        },
    }

    row = build_final_excel_rows(result)[0]

    assert row["TƯ CÁCH TỐ TỤNG"] == "Bị hại"
    assert row["QUAN HỆ PHÁP LUẬT"] == "Charge Synthetic A; Charge Synthetic B"

