from tests.sentence_test_support import parse_sentence


def test_probation_start_from_judgment() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”, "
        "cho hưởng án treo. Thời gian thử thách 04 năm, tính từ ngày tuyên án."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["probation_start_text"] == "tính từ ngày tuyên án"
    assert "thời gian thử thách 4 năm, tính từ ngày tuyên án" in sentence["display_text"]
    assert sentence["sentence_start_text"] == ""

