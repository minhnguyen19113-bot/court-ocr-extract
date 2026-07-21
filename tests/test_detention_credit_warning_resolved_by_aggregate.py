from tests.sentence_test_support import line, parse_sentence


def test_detention_credit_warning_resolved_by_aggregate() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Được trừ thời gian tạm giữ từ ngày chưa rõ."),
        line(7, 3, "Được trừ thời gian tạm giữ từ ngày 1/1/2099 đến ngày 2/1/2099."),
    ])

    assert "detention_credit_anchor_unparsed" not in output["warnings"]
    assert "01/01/2099" in output["defendant_sentence_map"]["defendant_alpha"]["detention_credit_text"]
