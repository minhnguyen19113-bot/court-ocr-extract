from tests.sentence_test_support import parse_sentence


def test_sentence_completeness_warning_additional_penalty() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”. "
        "Hình phạt bổ sung: chưa xác định."
    )
    assert "additional_penalty_anchor_unparsed" in output["warnings"]

