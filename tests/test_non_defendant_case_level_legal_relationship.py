from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import (
    DECISION_TAIL,
    FRONT_PRE_CONTENT,
    MIDDLE_EXCLUDED,
)


REVIEW_NOTE = "Chưa xác định tội danh liên quan trực tiếp đến bị hại"


def test_victim_does_not_receive_case_level_charges_without_specific_evidence() -> None:
    row = build_final_excel_rows(_result())[0]

    assert row["TƯ CÁCH TỐ TỤNG"] == "Bị hại"
    assert row["QUAN HỆ PHÁP LUẬT"] == ""
    assert REVIEW_NOTE in row["GHI CHÚ"]


def test_victim_receives_only_entity_specific_decision_tail_charge() -> None:
    result = _result()
    result["charge_output"]["victim_charge_evidence"] = [
        {
            "victim_entity_id": "victim_001",
            "normalized_charge": "Charge Synthetic A",
            "source_region": DECISION_TAIL,
        },
        {
            "victim_entity_id": "victim_other",
            "normalized_charge": "Charge Synthetic B",
            "source_region": DECISION_TAIL,
        },
        {
            "victim_entity_id": "victim_001",
            "normalized_charge": "Charge Synthetic Excluded",
            "source_region": MIDDLE_EXCLUDED,
        },
    ]

    row = build_final_excel_rows(result)[0]

    assert row["QUAN HỆ PHÁP LUẬT"] == "Charge Synthetic A"
    assert REVIEW_NOTE not in row["GHI CHÚ"]


def test_victim_specific_evidence_can_match_normalized_name() -> None:
    result = _result()
    result["charge_output"]["victim_charge_evidence"] = [
        {
            "normalized_victim_name": "person synthetic victim",
            "charge": "Charge Synthetic B",
            "source_region": DECISION_TAIL,
        }
    ]

    row = build_final_excel_rows(result)[0]

    assert row["QUAN HỆ PHÁP LUẬT"] == "Charge Synthetic B"
    assert REVIEW_NOTE not in row["GHI CHÚ"]


def _result() -> dict:
    charges = ["Charge Synthetic A", "Charge Synthetic B"]
    return {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "participants": [
            {
                "entity_id": "victim_001",
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
