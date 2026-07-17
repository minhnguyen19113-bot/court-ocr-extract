from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_six_candidates_produce_six_mappings_and_two_unique_charges() -> None:
    defendants = [
        {
            "entity_id": f"defendant_{index}",
            "full_name": f"Person Synthetic {index}",
        }
        for index in range(1, 7)
    ]
    lines = [
        {
            "line_id": f"p009_l{index:04d}",
            "page_number": 9,
            "reading_order": index - 1,
            "text": (
                f"{index}. Xử phạt bị cáo Person Synthetic {index} 12 tháng tù "
                f"về tội “Charge Synthetic {'Alpha' if index <= 3 else 'Beta'}”."
            ),
        }
        for index in range(1, 7)
    ]

    output = parse_explicit_decision_charges(lines, defendants=defendants)

    assert output["case_charges"] == [
        "Charge Synthetic Alpha",
        "Charge Synthetic Beta",
    ]
    assert output["verdict_candidate_count"] == 6
    assert output["parsed_charge_count"] == 6
    assert output["mapped_defendant_count"] == 6
    assert output["unmapped_verdict_count"] == 0
    assert output["invalid_charge_count"] == 0
    assert len(output["charge_evidence"]) == 6
    assert set(output["defendant_charge_map"]) == {
        f"defendant_{index}" for index in range(1, 7)
    }
