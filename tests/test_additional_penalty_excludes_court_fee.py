from tests.sentence_test_support import line, parse_sentence


def test_additional_penalty_excludes_court_fee() -> None:
    output = parse_sentence(
        [
            line(9, 1, "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”."),
            line(9, 2, "1.3. Hình phạt bổ sung:"),
            line(9, 3, "Án phí: bị cáo Person Synthetic Alpha phải chịu 200.000 đồng."),
        ]
    )
    assert output["defendant_sentence_map"]["defendant_alpha"]["additional_penalties"] == []

