from tests.sentence_test_support import DEFENDANTS, parse_sentence


def test_sentence_collective_each_defendant() -> None:
    output = parse_sentence(
        "Xử phạt các bị cáo Person Synthetic Alpha và Person Synthetic Beta, "
        "mỗi bị cáo 12 tháng tù về tội “Charge Synthetic”.",
        DEFENDANTS,
    )
    assert set(output["defendant_sentence_map"]) == {"defendant_alpha", "defendant_beta"}
    assert all(
        item["primary_penalty_text"] == "12 tháng tù"
        for item in output["defendant_sentence_map"].values()
    )
