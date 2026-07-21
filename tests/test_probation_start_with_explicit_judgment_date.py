from tests.sentence_test_support import parse_sentence


def test_probation_start_with_explicit_judgment_date() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 18 tháng, "
        "tính từ ngày tuyên án sơ thẩm (09/7/2099)."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["probation_start_text"] == "tính từ ngày tuyên án sơ thẩm 09/07/2099"
    assert sentence["sentence_start_text"] == ""

