from tests.sentence_test_support import parse_sentence


def test_sentence_start_duoc_tinh_tu_ngay() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”. "
        "Thời hạn tù được tính từ ngày 6/1/2099."
    )

    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["sentence_start_text"] == "thời hạn tù tính từ ngày 06/01/2099"
    assert "sentence_start_anchor_unparsed" not in output["warnings"]
