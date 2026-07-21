from tests.sentence_test_support import parse_sentence


def test_sentence_fine_primary() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha, hình phạt chính là phạt tiền "
        "50.000.000 đồng về tội “Charge Synthetic”."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["primary_penalty_kind"] == "fine"
    assert sentence["primary_penalty_text"] == "Phạt tiền 50.000.000 đồng"
