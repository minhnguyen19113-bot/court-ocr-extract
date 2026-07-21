from tests.sentence_test_support import parse_sentence


def test_name_disagreement_does_not_change_final_name() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpho 09 tháng tù về tội “Charge Synthetic”."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]

    assert sentence["defendant_names"] == ["Person Synthetic Alpha"]
    assert sentence["front_name"] == "Person Synthetic Alpha"
    assert sentence["decision_name"] == "Person Synthetic Alpho"
