from tests.sentence_test_support import parse_sentence


def test_sentence_term_imprisonment_year_month() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 03 (ba) năm 06 (sáu) tháng tù "
        "về tội “Charge Synthetic”."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["primary_penalty_kind"] == "term_imprisonment"
    assert sentence["duration_years"] == 3
    assert sentence["duration_months"] == 6
    assert sentence["display_text"] == "3 năm 6 tháng tù"
