from tests.sentence_test_support import line, parse_sentence


def test_sentence_raw_text_built_from_clause_spans() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù."),
        line(7, 2, "Thời hạn tù được tính kể từ ngày 6/1/2099."),
    ])

    for evidence in output["sentence_evidence"]:
        assert evidence["raw_text"] == "\n".join(
            span["raw_clause"] for span in evidence["clause_spans"]
        )
