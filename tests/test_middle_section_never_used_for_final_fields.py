from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges
from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import (
    DECISION_TAIL,
    FRONT_PRE_CONTENT,
    MIDDLE_EXCLUDED,
)


def test_middle_charge_and_middle_entity_are_ignored() -> None:
    defendants = [
        {
            "entity_id": "defendant_001",
            "full_name": "Person Synthetic Alpha",
            "source_region": FRONT_PRE_CONTENT,
        }
    ]
    parsed = parse_explicit_decision_charges(
        [
            {
                "line_id": "p004_l0001",
                "source_region": MIDDLE_EXCLUDED,
                "text": (
                    "Tuyên bị cáo Person Synthetic Alpha phạm tội "
                    '"Charge Synthetic Misleading".'
                ),
            },
            {
                "line_id": "p009_l0001",
                "page_number": 9,
                "source_region": DECISION_TAIL,
                "text": (
                    "Tuyên bị cáo Person Synthetic Alpha phạm tội "
                    '"Charge Synthetic Allowed".'
                ),
            },
        ],
        defendants=defendants,
    )

    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            *defendants,
            {
                "entity_id": "defendant_middle",
                "full_name": "Person Synthetic Middle",
                "source_region": MIDDLE_EXCLUDED,
            },
        ],
        "case_charges": parsed["case_charges"],
        "defendant_charge_map": parsed["defendant_charge_map"],
        "charge_output": parsed,
    }
    rows = build_final_excel_rows(result)

    assert parsed["case_charges"] == ["Charge Synthetic Allowed"]
    assert len(rows) == 1
    assert rows[0]["HỌ TÊN ĐƯƠNG SỰ"] == "Person Synthetic Alpha"
    assert rows[0]["QUAN HỆ PHÁP LUẬT"] == "Charge Synthetic Allowed"

