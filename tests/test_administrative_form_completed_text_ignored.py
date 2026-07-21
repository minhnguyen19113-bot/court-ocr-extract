from tests.sentence_test_support import line, parse_sentence


def test_administrative_form_completed_text_ignored() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Danh sách người bị kết án"),
        line(7, 3, "Đã chấp hành xong hình phạt tù."),
    ])

    assert not output["defendant_sentence_map"]["defendant_alpha"]["completion_text"]
    assert "completion_anchor_unparsed" not in output["warnings"]
