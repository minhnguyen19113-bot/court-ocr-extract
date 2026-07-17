from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_defendant_rows_receive_only_entity_specific_charges() -> None:
    result = _result()
    rows = build_final_excel_rows(result)

    assert {
        row["HỌ TÊN ĐƯƠNG SỰ"]: row["QUAN HỆ PHÁP LUẬT"]
        for row in rows
    } == {
        "Person Synthetic Alpha": "Charge Synthetic A",
        "Person Synthetic Beta": "Charge Synthetic A",
        "Person Synthetic Gamma": "Charge Synthetic B",
    }


def _result() -> dict:
    charges = ["Charge Synthetic A", "Charge Synthetic B"]
    evidence = [
        {
            "charge": charge,
            "source_region": DECISION_TAIL,
            "line_ids": [f"p010_l{index:04d}"],
        }
        for index, charge in enumerate(charges, start=1)
    ]
    return {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            {
                "entity_id": f"defendant_{index:03d}",
                "full_name": name,
                "source_region": FRONT_PRE_CONTENT,
            }
            for index, name in enumerate(
                [
                    "Person Synthetic Alpha",
                    "Person Synthetic Beta",
                    "Person Synthetic Gamma",
                ],
                start=1,
            )
        ],
        "case_charges": charges,
        "defendant_charge_map": {
            "defendant_001": ["Charge Synthetic A"],
            "defendant_002": ["Charge Synthetic A"],
            "defendant_003": ["Charge Synthetic B"],
        },
        "charge_output": {
            "case_charges": charges,
            "defendant_charge_map": {},
            "charge_evidence": evidence,
            "warnings": [],
        },
    }

