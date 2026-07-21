from tests.sentence_test_support import parse_sentence


def test_sentence_release_at_trial() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”. "
        "Tuyên bố trả tự do ngay tại phiên tòa cho bị cáo Person Synthetic Alpha."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["release_text"] == "được trả tự do tại phiên tòa"
