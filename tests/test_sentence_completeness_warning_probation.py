from tests.sentence_test_support import parse_sentence


def test_sentence_completeness_warning_probation() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 04 năm, 06."
    )
    assert "probation_duration_partial" in output["warnings"]

