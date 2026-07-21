from tests.sentence_test_support import line, parse_sentence


def test_probation_evidence_stops_before_violation_instruction() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 12 tháng tù, cho hưởng án treo."),
        line(7, 2, "Thời gian thử thách 24 tháng."),
        line(7, 3, "Trong thời gian thử thách, người được hưởng án treo cố ý vi phạm nghĩa vụ."),
    ])
    probation = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "probation")

    assert "vi phạm" not in probation["raw_text"]
    assert "p007_l0003" not in probation["line_ids"]
