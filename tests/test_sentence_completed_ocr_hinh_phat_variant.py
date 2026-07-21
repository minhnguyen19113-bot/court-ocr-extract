from tests.sentence_test_support import parse_sentence


def test_sentence_completed_ocr_hinh_phat_variant() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”. "
        "Đã chấp hành xong hình phát tù."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["execution_status"] == "completed"
    assert sentence["completion_text"] == "đã chấp hành xong hình phạt tù"

