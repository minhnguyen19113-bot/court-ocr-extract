from tests.sentence_test_support import line, parse_sentence


def test_administrative_tail_not_sentence_candidate() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Xác nhận hiện trạng hồ sơ"),
        line(7, 3, "Xử phạt bị cáo Person Synthetic Alpha 99 năm tù."),
    ])

    assert output["defendant_sentence_map"]["defendant_alpha"]["primary_penalty_text"] == "3 năm tù"
    assert output["diagnostics"]["sentence_candidate_count"] == 1
