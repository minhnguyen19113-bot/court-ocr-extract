from tests.sentence_test_support import line, parse_sentence


def test_completion_warning_resolved_by_aggregate() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Thời hạn tù bằng thời gian chưa rõ."),
        line(7, 3, "Thời hạn tù bằng với thời gian tạm giam."),
    ])

    assert "completion_anchor_unparsed" not in output["warnings"]
    assert output["defendant_sentence_map"]["defendant_alpha"]["completion_text"]
