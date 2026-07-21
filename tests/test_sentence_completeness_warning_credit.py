from tests.sentence_test_support import parse_sentence


def test_sentence_completeness_warning_credit() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”. "
        "Được trừ thời gian tạm giữ, tạm giam từ ngày chưa rõ đến ngày chưa rõ."
    )
    assert "detention_credit_anchor_unparsed" in output["warnings"]

