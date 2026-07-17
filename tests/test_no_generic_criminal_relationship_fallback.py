from __future__ import annotations

from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_criminal_case_without_explicit_charge_stays_blank() -> None:
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {"legal_relationship": "Hình sự"},
        "trial_panel": {},
        "defendants": [
            {
                "entity_id": "defendant_a",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Người Synthetic A",
                "birth_date_or_year": "1990",
            }
        ],
    }

    row = build_final_excel_rows(result)[0]

    assert row["LOẠI ÁN"] == "Hình sự sơ thẩm"
    assert row["QUAN HỆ PHÁP LUẬT"] == ""
    assert "Chưa gắn chắc tội danh với bị cáo từ phần Quyết định" in row["GHI CHÚ"]


def test_explicit_entity_charges_fill_defendant_relationship_in_order() -> None:
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "case_charges": ["Tội Synthetic Alpha", "Tội Synthetic Beta"],
        "defendant_charge_map": {
            "defendant_a": ["Tội Synthetic Alpha", "Tội Synthetic Beta"]
        },
        "charge_output": {
            "charge_evidence": [
                {
                    "charge": "Tội Synthetic Alpha",
                    "source_region": DECISION_TAIL,
                },
                {
                    "charge": "Tội Synthetic Beta",
                    "source_region": DECISION_TAIL,
                },
            ]
        },
        "defendants": [
            {
                "entity_id": "defendant_a",
                "source_region": FRONT_PRE_CONTENT,
                "full_name": "Người Synthetic A",
                "birth_date_or_year": "1990",
            }
        ],
    }

    row = build_final_excel_rows(result)[0]

    assert row["QUAN HỆ PHÁP LUẬT"] == "Tội Synthetic Alpha; Tội Synthetic Beta"
    assert "Chưa gắn chắc tội danh" not in row["GHI CHÚ"]
