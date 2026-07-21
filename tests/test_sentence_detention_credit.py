from tests.sentence_test_support import parse_sentence


def test_sentence_detention_credit() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”; "
        "được trừ thời gian tạm giữ, tạm giam từ ngày 12/2/2099 đến ngày 6/6/2099."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["detention_credit_text"] == (
        "được trừ thời gian tạm giữ, tạm giam từ ngày 12/02/2099 đến ngày 06/06/2099"
    )
