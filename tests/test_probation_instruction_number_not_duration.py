from tests.sentence_test_support import line, parse_sentence


def test_probation_instruction_number_not_duration() -> None:
    output = parse_sentence([
        line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha 12 tháng tù, cho hưởng án treo."),
        line(7, 2, "Trong thời gian thử thách, nếu cố ý vi phạm nghĩa vụ 02 lần thì xử lý theo quy định."),
    ])
    sentence = output["defendant_sentence_map"]["defendant_alpha"]

    assert sentence["probation_duration_months"] is None
    assert sentence["probation_duration_years"] is None
