from tests.sentence_test_support import parse_sentence


def test_sentence_start_from_execution() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm 06 tháng tù về tội “Charge Synthetic”. "
        "Thời hạn tù tính từ ngày bắt bị cáo chấp hành án."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["sentence_start_text"] == "thời hạn tù tính từ ngày bắt chấp hành án"
