from tests.sentence_test_support import line, parse_sentence


def test_sentence_cross_page_continuation() -> None:
    output = parse_sentence(
        [
            line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm 06 tháng tù về tội “Charge"),
            line(7, 2, "8"),
            line(8, 1, "Synthetic”. Thời hạn tù tính từ ngày 6/1/2099."),
        ]
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["line_ids"] == ["p007_l0001", "p008_l0001"]
    assert sentence["sentence_start_text"].endswith("06/01/2099")
