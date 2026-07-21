from tests.sentence_test_support import parse_sentence


def test_name_normalization_only_no_disagreement() -> None:
    output = parse_sentence("Xử phạt bị cáo PERSON   SYNTHETIC   ALPHA 09 tháng tù.")
    evidence = output["sentence_evidence"][0]

    assert evidence["match_method"] == "normalization_only"
    assert "cross_source_person_name_disagreement" not in output["warnings"]
