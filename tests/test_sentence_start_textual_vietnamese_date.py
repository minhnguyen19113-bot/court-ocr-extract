from tests.sentence_test_support import parse_sentence


def test_sentence_start_textual_vietnamese_date() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”. "
        "Thời hạn tù tính từ ngày 16 tháng 3 năm 2099."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["sentence_start_text"] == "thời hạn tù tính từ ngày 16/03/2099"

