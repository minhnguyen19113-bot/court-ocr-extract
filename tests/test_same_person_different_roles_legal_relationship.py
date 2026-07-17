from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_same_person_defendant_and_victim_keeps_role_specific_relationships() -> None:
    charges = ["Charge Synthetic A", "Charge Synthetic B"]
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            {
                "entity_id": "defendant_001",
                "full_name": "Person Synthetic Shared",
                "source_region": FRONT_PRE_CONTENT,
            }
        ],
        "participants": [
            {
                "role": "Bị hại",
                "full_name": "Person Synthetic Shared",
                "source_region": FRONT_PRE_CONTENT,
            }
        ],
        "case_charges": charges,
        "defendant_charge_map": {"defendant_001": ["Charge Synthetic A"]},
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

    rows = build_final_excel_rows(result)

    assert len(rows) == 2
    assert {
        row["TƯ CÁCH TỐ TỤNG"]: row["QUAN HỆ PHÁP LUẬT"]
        for row in rows
    } == {
        "Bị cáo": "Charge Synthetic A",
        "Bị hại": "Charge Synthetic A; Charge Synthetic B",
    }

