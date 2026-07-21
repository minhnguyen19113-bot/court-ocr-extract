from tests.sentence_test_support import parse_sentence


def test_sentence_non_custodial_reform() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 18 tháng cải tạo không giam giữ "
        "về tội “Charge Synthetic”."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["primary_penalty_kind"] == "non_custodial_reform"
    assert sentence["primary_penalty_text"] == "18 tháng cải tạo không giam giữ"
