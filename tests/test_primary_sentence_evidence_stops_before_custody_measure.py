from tests.sentence_test_support import line, parse_sentence


def test_primary_sentence_evidence_stops_before_custody_measure() -> None:
    output = parse_sentence([
        line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."),
        line(8, 2, "Tiếp tục tạm giam bị cáo trong thời hạn 45 ngày."),
    ])
    primary = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "primary_penalty")
    assert primary["line_ids"] == ["p008_l0001"]
    assert "tạm giam" not in primary["raw_text"]

