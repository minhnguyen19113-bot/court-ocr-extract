from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_open_quote_prevents_bounded_candidate_split() -> None:
    output = parse_explicit_decision_charges(
        "\n".join(
            [
                "Xử phạt bị cáo Person Synthetic Alpha về tội “Charge Synthetic",
                "bị cáo Phrase Synthetic phạm tội Fragment",
                "Value”.",
            ]
        ),
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["verdict_candidate_count"] == 1
    assert output["parsed_charge_count"] == 1
    assert output["charge_evidence"][0]["raw_charge"] == (
        "Charge Synthetic\nbị cáo Phrase Synthetic phạm tội Fragment\nValue"
    )


def test_unterminated_quote_is_rejected_at_block_guard() -> None:
    output = parse_explicit_decision_charges(
        "Xử phạt bị cáo Person Synthetic Alpha về tội “Charge Synthetic",
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == []
    assert output["verdict_candidate_count"] == 0
    assert "unterminated_quoted_charge" in output["warnings"]
