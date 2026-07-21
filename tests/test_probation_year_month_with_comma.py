from tests.sentence_test_support import parse_sentence


def test_probation_year_month_with_comma() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 04 năm, 06 tháng."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["probation_duration_years"] == 4
    assert sentence["probation_duration_months"] == 6
    assert sentence["probation_text"] == "thời gian thử thách 4 năm 6 tháng"

