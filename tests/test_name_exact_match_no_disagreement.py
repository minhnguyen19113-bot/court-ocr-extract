from tests.sentence_test_support import parse_sentence


def test_name_exact_match_no_disagreement() -> None:
    output = parse_sentence("Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù.")
    evidence = output["sentence_evidence"][0]

    assert evidence["match_method"] == "exact"
    assert "cross_source_person_name_disagreement" not in output["warnings"]
