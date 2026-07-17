from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_unquoted_verdict_stops_before_following_legal_phrase() -> None:
    output = parse_explicit_decision_charges(
        (
            "Tuyên bị cáo Person Synthetic Alpha phạm tội Charge Synthetic Alpha "
            "theo quy định tại Điều synthetic."
        ),
        defendants=[
            {"entity_id": "defendant_001", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == ["Charge Synthetic Alpha"]
    assert output["defendant_charge_map"] == {
        "defendant_001": ["Charge Synthetic Alpha"]
    }
    evidence = output["charge_evidence"][0]
    assert evidence["source_region"] == "decision_tail"
    assert "unquoted" in evidence["match_method"]


def test_unquoted_sentence_for_charge_does_not_include_penalty() -> None:
    output = parse_explicit_decision_charges(
        "Xử phạt bị cáo Person Synthetic Alpha 12 tháng tù về tội Charge Synthetic Beta.",
        defendants=[
            {"entity_id": "defendant_001", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == ["Charge Synthetic Beta"]

