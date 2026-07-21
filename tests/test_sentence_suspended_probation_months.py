from tests.sentence_test_support import parse_sentence


def test_sentence_suspended_probation_months() -> None:
    output = parse_sentence(
        "Tuyên phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, "
        "được hưởng án treo; thời gian thử thách là 18 tháng."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["probation_duration_months"] == 18
    assert "thời gian thử thách 18 tháng" in sentence["display_text"]
