from tests.sentence_test_support import line, parse_sentence


def test_probation_evidence_stops_before_ubnd_supervision() -> None:
    output = parse_sentence([
        line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, cho hưởng án treo."),
        line(8, 2, "Thời gian thử thách 18 tháng, tính từ ngày tuyên án."),
        line(8, 3, "Giao bị cáo cho Ủy ban nhân dân giám sát, giáo dục."),
    ])
    probation = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "probation")
    assert probation["line_ids"] == ["p008_l0001", "p008_l0002"]
    assert "Ủy ban nhân dân" not in probation["raw_text"]

