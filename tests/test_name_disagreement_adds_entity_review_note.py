from court_ocr_extract.final_excel_builder import _row_sentence


def test_name_disagreement_adds_entity_review_note() -> None:
    value, notes = _row_sentence(
        role="Bị cáo",
        entity={"entity_id": "defendant_alpha"},
        is_defendant=True,
        defendant_sentence_map={
            "defendant_alpha": {
                "primary_penalty_text": "9 tháng tù",
                "warnings": ["cross_source_person_name_disagreement"],
            }
        },
        decision_tail_status="success",
    )

    assert value == "9 tháng tù"
    assert notes == ["Tên giữa phần đầu và Quyết định không thống nhất, cần đối chiếu"]
