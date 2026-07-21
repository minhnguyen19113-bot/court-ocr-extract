from tests.sentence_test_support import parse_sentence


def test_sentence_time_equal_detention() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”. "
        "Thời hạn tù bằng với thời gian tạm giam."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["execution_status"] == "completed"
    assert sentence["completion_text"] == "thời hạn tù bằng thời gian tạm giam"
    assert sentence["sentence_start_text"] == ""

