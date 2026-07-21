from tests.sentence_test_support import parse_sentence


def test_sentence_time_served_completed() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng 01 ngày tù về tội “Charge Synthetic”. "
        "Thời hạn tù bằng thời gian tạm giam; đã chấp hành xong hình phạt tù."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["completion_text"] == (
        "thời hạn tù bằng thời gian tạm giam; "
        "đã chấp hành xong hình phạt tù"
    )
    assert "đã chấp hành xong hình phạt tù" in sentence["display_text"]
