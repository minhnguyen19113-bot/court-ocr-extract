from tests.sentence_test_support import line, parse_sentence


def test_additional_penalty_separate_decision_item() -> None:
    output = parse_sentence(
        [
            line(9, 1, "Xử phạt bị cáo Person Synthetic Alpha 11 tháng tù về tội “Charge Synthetic”."),
            line(9, 2, "1.3. Hình phát bổ sung:"),
            line(9, 3, "Phát bổ sung bị cáo Person Synthetic Alpha 30.000.000 đồng"),
            line(9, 4, "để sung công quỹ Nhà nước."),
        ]
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["additional_penalties"] == ["phạt tiền 30.000.000 đồng"]
    assert output["diagnostics"]["additional_penalty_count"] == 1
    assert any("p009_l0003" in item["line_ids"] for item in output["sentence_evidence"])

