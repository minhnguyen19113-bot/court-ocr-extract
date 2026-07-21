from tests.sentence_test_support import parse_sentence


def test_sentence_month_day_duration() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 11 tháng 01 ngày tù về tội “Charge Synthetic”."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["duration_months"] == 11
    assert sentence["duration_days"] == 1
    assert sentence["primary_penalty_text"] == "11 tháng 1 ngày tù"
