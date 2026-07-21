from tests.sentence_test_support import DEFENDANTS, parse_sentence


def test_sentence_different_terms_same_block() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 12 tháng tù, bị cáo "
        "Person Synthetic Beta 18 tháng tù về tội “Charge Synthetic”.",
        DEFENDANTS,
    )
    assert output["defendant_sentence_map"]["defendant_alpha"]["primary_penalty_text"] == "12 tháng tù"
    assert output["defendant_sentence_map"]["defendant_beta"]["primary_penalty_text"] == "18 tháng tù"
