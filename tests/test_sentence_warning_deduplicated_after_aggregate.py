from tests.sentence_test_support import line, parse_sentence


def test_sentence_warning_deduplicated_after_aggregate() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù."),
        line(7, 2, "Thời hạn tù tính từ ngày chưa rõ."),
        line(7, 3, "Thời hạn tù được tính từ ngày chưa xác định."),
    ])
    warnings = [item for item in output["sentence_warnings"] if item["warning"] == "sentence_start_anchor_unparsed"]

    assert len(warnings) == 1
    assert warnings[0]["scope"] == "entity"
