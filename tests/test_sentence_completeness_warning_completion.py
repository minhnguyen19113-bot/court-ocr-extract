from tests.sentence_test_support import parse_sentence


def test_sentence_completeness_warning_completion() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”. "
        "Đã chấp hành xong hình phạt."
    )
    assert "completion_anchor_unparsed" in output["warnings"]

