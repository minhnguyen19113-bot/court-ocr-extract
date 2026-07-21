from tests.sentence_test_support import parse_sentence


def test_sentence_release_does_not_imply_suspended() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”. "
        "Trả tự do tại phiên tòa cho bị cáo Person Synthetic Alpha."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["suspended"] is False
    assert sentence["primary_penalty_kind"] == "term_imprisonment"
