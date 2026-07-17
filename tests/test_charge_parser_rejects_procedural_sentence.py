from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_procedural_sentence_is_rejected_as_charge() -> None:
    output = parse_explicit_decision_charges(
        (
            "Tuyên bị cáo Person Synthetic Alpha phạm tội "
            '“Tòa án buộc người đó chấp hành hình phạt của bản án trước”.'
        ),
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == []
    assert output["defendant_charge_map"] == {}
    assert output["invalid_charge_count"] == 1
    assert "invalid_charge_candidate_rejected" in output["warnings"]
    assert "verdict_charge_coverage_incomplete:0/1" in output["warnings"]
