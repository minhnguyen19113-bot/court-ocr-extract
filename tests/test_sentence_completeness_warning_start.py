from tests.sentence_test_support import parse_sentence


def test_sentence_completeness_warning_start() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”. "
        "Thời hạn tù tính từ ngày chưa xác định."
    )
    assert "sentence_start_anchor_unparsed" in output["warnings"]

