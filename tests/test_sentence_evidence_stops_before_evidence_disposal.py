from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_stops_before_evidence_disposal() -> None:
    output = parse_sentence(
        [
            line(9, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."),
            line(9, 2, "Thời hạn tù tính từ ngày 16/3/2099."),
            line(9, 3, "2. Xử lý vật chứng: tịch thu vật synthetic."),
            line(9, 4, "3. Án phí: nghĩa vụ synthetic."),
        ]
    )
    for evidence in output["sentence_evidence"]:
        assert "Xử lý vật chứng" not in evidence["raw_text"]
        assert "p009_l0003" not in evidence["line_ids"]
        assert "p009_l0004" not in evidence["line_ids"]

