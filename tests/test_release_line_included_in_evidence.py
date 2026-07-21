from tests.sentence_test_support import line, parse_sentence


def test_release_line_included_in_evidence() -> None:
    release_id = "p009_l0002"
    output = parse_sentence(
        [
            line(9, 1, "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."),
            line(9, 2, "Tuyên bố trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa."),
        ]
    )
    assert output["defendant_sentence_map"]["defendant_alpha"]["release_text"]
    assert any(
        release_id in item["line_ids"] and "trả tự do" in item["raw_text"]
        for item in output["sentence_evidence"]
    )

