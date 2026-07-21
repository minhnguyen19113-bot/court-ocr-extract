from tests.sentence_test_support import parse_sentence


def test_sentence_does_not_calculate_aggregate() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge One”.\n"
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Two”."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["aggregate_penalty_text"] == ""
    assert "5 năm tù" not in sentence["display_text"]
    assert "multiple_primary_sentences_without_aggregate" in output["warnings"]
