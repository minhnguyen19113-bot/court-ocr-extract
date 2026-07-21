from tests.sentence_test_support import parse_sentence


def test_sentence_aggregate_prefers_final_common_penalty() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”; "
        "tổng hợp hình phạt, buộc bị cáo Person Synthetic Alpha phải chấp hành "
        "hình phạt chung là 05 năm tù."
    )
    sentence = output["defendant_sentence_map"]["defendant_alpha"]
    assert sentence["aggregate_penalty_text"] == "Hình phạt chung: 5 năm tù"
    assert sentence["display_text"].startswith("Hình phạt chung: 5 năm tù")
