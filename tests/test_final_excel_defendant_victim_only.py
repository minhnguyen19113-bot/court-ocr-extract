from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_final_excel_contains_only_defendant_and_victim_rows() -> None:
    charge = "Charge Synthetic Alpha"
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {
            "judgment_number": "901/2099/HS-ST",
            "judgment_date": "01/02/2099",
        },
        "trial_panel": {},
        "defendants": [
            {
                "entity_id": "defendant_alpha",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Person Synthetic Shared",
            }
        ],
        "participants": [
            {
                "role": "Bị hại",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Person Synthetic Shared",
            },
            {
                "role": "Nguyên đơn dân sự",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Person Synthetic Civil",
            },
            {
                "role": "Người làm chứng",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Person Synthetic Witness",
            },
        ],
        "case_charges": [charge],
        "defendant_charge_map": {"defendant_alpha": [charge]},
        "charge_output": {
            "charge_evidence": [
                {"charge": charge, "source_region": DECISION_TAIL}
            ]
        },
    }

    rows = build_final_excel_rows(result)

    assert [row["TƯ CÁCH TỐ TỤNG"] for row in rows] == ["Bị cáo", "Bị hại"]
    assert len(rows) == 2
