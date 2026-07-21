from tests.sentence_test_support import parse_sentence


def test_probation_duration_year_only_not_partial() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 18 tháng tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 3 năm."
    )
    assert "probation_duration_partial" not in output["warnings"]

