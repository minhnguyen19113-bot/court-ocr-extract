from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_single_line_clause_offsets() -> None:
    text = (
        "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”; "
        "Thời hạn tù được tính từ ngày 6/1/2099."
    )
    output = parse_sentence([line(7, 1, text)])
    evidence = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "sentence_start")
    span = evidence["clause_spans"][0]

    assert span["char_start"] == text.index("Thời hạn tù")
    assert text[span["char_start"]:span["char_end"]] == span["raw_clause"]
    assert evidence["raw_clause"] == span["raw_clause"]
