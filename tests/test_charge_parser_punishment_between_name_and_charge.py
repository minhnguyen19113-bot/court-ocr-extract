from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_punishment_phrase_between_name_and_charge_does_not_pollute_name() -> None:
    output = parse_explicit_decision_charges(
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm 06 tháng tù "
        "về tội ‘Charge Synthetic Alpha’.",
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == ["Charge Synthetic Alpha"]
    assert output["defendant_charge_map"] == {
        "defendant_alpha": ["Charge Synthetic Alpha"]
    }
    assert "exact_normalized_full_name" in output["charge_evidence"][0]["match_method"]
