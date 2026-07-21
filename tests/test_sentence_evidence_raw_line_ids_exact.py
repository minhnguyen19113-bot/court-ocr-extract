from tests.sentence_test_support import line, parse_sentence


def test_sentence_evidence_raw_line_ids_exact() -> None:
    lines = [
        line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, cho hưởng án treo."),
        line(8, 2, "Thời gian thử thách 18 tháng."),
        line(8, 3, "Tính từ ngày tuyên án sơ thẩm (09/7/2099)."),
        line(8, 4, "1.3. Hình phạt bổ sung:"),
        line(8, 5, "Phạt bổ sung bị cáo Person Synthetic Alpha 30.000.000 đồng."),
    ]
    output = parse_sentence(lines)
    for evidence in output["sentence_evidence"]:
        assert evidence["raw_text"] == "\n".join(
            span["raw_clause"] for span in evidence["clause_spans"]
        )
        assert evidence["line_ids"] == list(
            dict.fromkeys(span["line_id"] for span in evidence["clause_spans"])
        )
