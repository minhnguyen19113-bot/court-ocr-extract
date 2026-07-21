from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_multiline_clause_offsets() -> None:
    lines = [
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù."),
        line(7, 2, "Được trừ thời gian tạm giữ từ ngày 1/1/2099"),
        line(7, 3, "đến ngày 2/1/2099."),
    ]
    output = parse_sentence(lines)
    evidence = next(item for item in output["sentence_evidence"] if item["evidence_type"] == "detention_credit")

    assert evidence["line_ids"] == ["p007_l0002", "p007_l0003"]
    assert len(evidence["clause_spans"]) == 2
    for span in evidence["clause_spans"]:
        assert span["raw_line_text"][span["char_start"]:span["char_end"]] == span["raw_clause"]
