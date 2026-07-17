from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_known_front_dictionary_maps_multiple_defendants_without_blind_split() -> None:
    defendants = [
        {"entity_id": "defendant_001", "full_name": "Person Synthetic Alpha"},
        {"entity_id": "defendant_002", "full_name": "Person Synthetic Beta"},
        {"entity_id": "defendant_003", "full_name": "Person Synthetic Gamma"},
    ]
    output = parse_explicit_decision_charges(
        [
            {
                "line_id": "p010_l0001",
                "page_number": 10,
                "text": (
                    "Tuyên các bị cáo Person Synthetic Alpha, Person Synthetic Beta "
                    'phạm tội "Charge Synthetic A".'
                ),
            },
            {
                "line_id": "p010_l0002",
                "page_number": 10,
                "text": (
                    "Tuyên bị cáo Person Synthetic Gamma phạm tội "
                    '"Charge Synthetic B".'
                ),
            },
        ],
        defendants=defendants,
    )

    assert output["case_charges"] == ["Charge Synthetic A", "Charge Synthetic B"]
    assert output["defendant_charge_map"] == {
        "defendant_001": ["Charge Synthetic A"],
        "defendant_002": ["Charge Synthetic A"],
        "defendant_003": ["Charge Synthetic B"],
    }
    assert output["charge_evidence"][0]["defendant_entity_ids"] == [
        "defendant_001",
        "defendant_002",
    ]


def test_unresolved_collective_phrase_is_not_assigned() -> None:
    output = parse_explicit_decision_charges(
        'Tuyên các bị cáo còn lại phạm tội "Charge Synthetic A".',
        defendants=[
            {"entity_id": "defendant_001", "full_name": "Person Synthetic Alpha"},
            {"entity_id": "defendant_002", "full_name": "Person Synthetic Beta"},
        ],
    )

    assert output["case_charges"] == ["Charge Synthetic A"]
    assert output["defendant_charge_map"] == {}
    assert "unresolved_collective_defendant_charge_mapping" in output["warnings"]

