from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_ambiguous_fuzzy_name_is_warned_and_not_assigned() -> None:
    output = parse_explicit_decision_charges(
        'Tuyên bị cáo Person Synthetic Alpha phạm tội "Charge Synthetic A".',
        defendants=[
            {
                "entity_id": "defendant_001",
                "full_name": "Person Synthetic Alpha One",
            },
            {
                "entity_id": "defendant_002",
                "full_name": "Person Synthetic Alpha Two",
            },
        ],
        min_name_match_score=60.0,
        name_match_ambiguity_gap=10.0,
    )

    assert output["case_charges"] == ["Charge Synthetic A"]
    assert output["defendant_charge_map"] == {}
    assert "ambiguous_defendant_charge_mapping" in output["warnings"]

