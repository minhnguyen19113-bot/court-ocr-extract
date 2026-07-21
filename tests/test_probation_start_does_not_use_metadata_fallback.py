from tests.sentence_test_support import parse_sentence


def test_probation_start_does_not_use_metadata_fallback() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 18 tháng, tính từ ngày tuyên án."
    )
    start = output["defendant_sentence_map"]["defendant_alpha"]["probation_start_text"]
    assert start == "tính từ ngày tuyên án"
    assert "2099" not in start

