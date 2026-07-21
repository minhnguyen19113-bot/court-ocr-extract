from tests.sentence_test_support import parse_sentence


def test_sentence_life_imprisonment() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha tù chung thân về tội “Charge Synthetic”."
    )
    assert output["defendant_sentence_map"]["defendant_alpha"]["primary_penalty_kind"] == "life_imprisonment"
