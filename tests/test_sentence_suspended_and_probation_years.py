from tests.sentence_test_support import parse_sentence


def test_sentence_suspended_and_probation_years() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 01 năm 06 tháng tù về tội “Charge Synthetic”, "
        "cho hưởng án treo, thời gian thử thách 03 năm."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["primary_penalty_kind"] == "suspended_imprisonment"
    assert sentence["suspended"] is True
    assert sentence["execution_status"] == "suspended"
    assert sentence["probation_duration_years"] == 3
    assert sentence["display_text"] == (
        "1 năm 6 tháng tù, cho hưởng án treo; thời gian thử thách 3 năm"
    )


def test_sentence_suspended_can_recover_missing_tu_token() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 01 năm 06 tháng về tội “Charge Synthetic”, "
        "cho hưởng án treo; thời gian thử thách 03 năm."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["primary_penalty_kind"] == "suspended_imprisonment"
    assert sentence["primary_penalty_text"] == "1 năm 6 tháng tù"
