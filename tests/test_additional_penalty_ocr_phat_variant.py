from tests.sentence_test_support import parse_sentence


def test_additional_penalty_ocr_phat_variant() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”; "
        "hình phát bổ sung: phát bổ sung bị cáo Person Synthetic Alpha "
        "30.000.000 đồng."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["additional_penalties"] == ["phạt tiền 30.000.000 đồng"]

