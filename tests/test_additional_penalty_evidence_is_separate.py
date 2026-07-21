from tests.sentence_test_support import line, parse_sentence


def test_additional_penalty_evidence_is_separate() -> None:
    output = parse_sentence([
        line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”."),
        line(8, 2, "1.3. Hình phạt bổ sung:"),
        line(8, 3, "Phạt bổ sung bị cáo Person Synthetic Alpha 30.000.000 đồng."),
    ])
    primary = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "primary_penalty")
    additional = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "additional_penalty")
    assert primary["line_ids"] == ["p008_l0001"]
    assert additional["line_ids"] == ["p008_l0002", "p008_l0003"]

