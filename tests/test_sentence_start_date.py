from tests.sentence_test_support import parse_sentence


def test_sentence_start_date() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”. "
        "Thời hạn tù tính từ ngày 6/1/2099."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["sentence_start_text"] == "thời hạn tù tính từ ngày 06/01/2099"
    assert "06/01/2099" in sentence["display_text"]
