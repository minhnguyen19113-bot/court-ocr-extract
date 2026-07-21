from tests.sentence_test_support import DEFENDANTS, parse_sentence


def test_sentence_unresolved_collective_not_mapped() -> None:
    output = parse_sentence(
        "Xử phạt các bị cáo còn lại mỗi bị cáo 12 tháng tù về tội “Charge Synthetic”.",
        DEFENDANTS,
    )
    assert output["defendant_sentence_map"] == {}
    assert "unresolved_collective_defendant_sentence_mapping" in output["warnings"]
