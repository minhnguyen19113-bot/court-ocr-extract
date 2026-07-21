from tests.sentence_test_support import parse_sentence


def test_probation_duration_year_month_not_partial() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 4 năm 6 tháng."
    )
    assert "probation_duration_partial" not in output["warnings"]

