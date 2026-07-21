from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_raw_matches_line_ids() -> None:
    lines = [
        line(9, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."),
        line(9, 2, "Thời hạn tù tính từ ngày 16 tháng 3 năm 2099."),
    ]
    output = parse_sentence(lines)
    lookup = {item["line_id"]: item["text"] for item in lines}
    for evidence in output["sentence_evidence"]:
        assert evidence["raw_text"].splitlines() == [
            lookup[line_id] for line_id in evidence["line_ids"]
        ]

