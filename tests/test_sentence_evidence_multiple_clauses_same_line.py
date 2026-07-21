from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_multiple_clauses_same_line() -> None:
    text = (
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”; "
        "Thời hạn tù tính từ ngày 6/1/2099; "
        "Trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa."
    )
    output = parse_sentence([line(7, 1, text)])
    by_type = {item["evidence_type"]: item for item in output["sentence_evidence"]}

    assert by_type["sentence_start"]["raw_clause"].startswith("Thời hạn tù")
    assert "Trả tự do" not in by_type["sentence_start"]["raw_clause"]
    assert by_type["release"]["raw_clause"].startswith("Trả tự do")
    assert by_type["sentence_start"]["clause_spans"] != by_type["release"]["clause_spans"]
