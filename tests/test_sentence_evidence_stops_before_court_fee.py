from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_stops_before_court_fee() -> None:
    output = parse_sentence([
        line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."),
        line(8, 2, "Án phí: bị cáo phải chịu nghĩa vụ synthetic."),
    ])
    assert all("Án phí" not in item["raw_text"] for item in output["sentence_evidence"])
    assert all("p008_l0002" not in item["line_ids"] for item in output["sentence_evidence"])

