from tests.sentence_test_support import line, parse_sentence


def test_administrative_tail_not_completeness_warning() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Biên bản giao nhận"),
        line(7, 3, "Thời hạn tù tính từ ngày chưa rõ."),
    ])

    assert "sentence_start_anchor_unparsed" not in output["warnings"]
    assert all(item["line_ids"] != ["p007_l0003"] for item in output["sentence_evidence"])
