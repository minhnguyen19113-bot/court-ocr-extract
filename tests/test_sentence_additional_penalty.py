from tests.sentence_test_support import parse_sentence


def test_sentence_additional_penalty() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”; "
        "hình phạt bổ sung: phạt tiền 20.000.000 đồng."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["additional_penalties"] == ["phạt tiền 20.000.000 đồng"]
    assert "hình phạt bổ sung: phạt tiền 20.000.000 đồng" in sentence["display_text"]
