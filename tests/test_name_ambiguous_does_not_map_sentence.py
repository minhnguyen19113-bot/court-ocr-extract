from court_ocr_extract.sentence_parser import parse_defendant_sentences


def test_name_ambiguous_does_not_map_sentence() -> None:
    defendants = [
        {"entity_id": "defendant_one", "full_name": "Person Synthetic Alfa"},
        {"entity_id": "defendant_two", "full_name": "Person Synthetic Alfo"},
    ]
    output = parse_defendant_sentences(
        "Xử phạt bị cáo Person Synthetic Alfi 09 tháng tù về tội “Charge Synthetic”.",
        defendants=defendants,
        min_name_match_score=80,
    )

    assert output["defendant_sentence_map"] == {}
    assert "ambiguous_defendant_sentence_mapping" in output["warnings"]
    warning = next(item for item in output["sentence_warnings"] if item["warning"] == "ambiguous_defendant_sentence_mapping")
    assert warning["decision_raw_name"] == "Person Synthetic Alfi"
    assert warning["match_method"] == "ambiguous"
