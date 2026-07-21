from tests.sentence_test_support import line, parse_sentence


def test_resolved_warning_not_exported() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù."),
        line(7, 2, "Thời hạn tù tính từ ngày chưa rõ."),
        line(7, 3, "Thời hạn tù tính từ ngày 6/1/2099."),
    ])

    assert all(item["warning"] != "sentence_start_anchor_unparsed" for item in output["sentence_warnings"])
    assert all("sentence_start_anchor_unparsed" not in item["warnings"] for item in output["sentence_evidence"])
