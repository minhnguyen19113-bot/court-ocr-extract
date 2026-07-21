from tests.sentence_test_support import parse_sentence


def test_name_unique_fuzzy_disagreement_warning() -> None:
    output = parse_sentence(
        "Xử phạt bị cáo Person Synthetic Alpho 09 tháng tù về tội “Charge Synthetic”."
    )
    warning = next(item for item in output["sentence_warnings"] if item["warning"] == "cross_source_person_name_disagreement")

    assert warning["match_method"] == "unique_fuzzy"
    assert warning["front_name"] == "Person Synthetic Alpha"
    assert warning["decision_name"] == "Person Synthetic Alpho"
    assert warning["similarity"] < 100
