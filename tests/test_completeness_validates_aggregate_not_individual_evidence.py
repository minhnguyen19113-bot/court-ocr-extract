from tests.sentence_test_support import line, parse_sentence


def test_completeness_validates_aggregate_not_individual_evidence() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 03 năm tù về tội “Charge Synthetic”."),
        line(7, 2, "Thời hạn tù tính từ ngày chưa rõ."),
        line(7, 3, "Thời hạn tù được tính từ ngày 6/1/2099."),
    ])

    assert "sentence_start_anchor_unparsed" not in output["warnings"]
    assert output["defendant_sentence_map"]["defendant_alpha"]["sentence_start_text"].endswith("06/01/2099")
