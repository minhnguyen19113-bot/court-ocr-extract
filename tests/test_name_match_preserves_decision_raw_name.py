from tests.sentence_test_support import parse_sentence


def test_name_match_preserves_decision_raw_name() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person   Synthetic   Alpha 09 tháng tù về tội “Charge Synthetic”."
    )
    evidence = output["sentence_evidence"][0]

    assert evidence["decision_raw_name"] == "Person   Synthetic   Alpha"
    assert evidence["front_entity_name"] == "Person Synthetic Alpha"
    assert evidence["decision_names"] == ["Person   Synthetic   Alpha"]
