from court_ocr_extract.final_excel_builder import build_final_excel_rows


def test_field_validator_warning_still_adds_correct_entity_note() -> None:
    rows = build_final_excel_rows({
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            {"full_name": "Person Synthetic Alpha", "warnings": ["entity_field_rejected:address"]},
            {"full_name": "Person Synthetic Beta", "warnings": []},
        ],
    })
    by_name = {row["HỌ TÊN ĐƯƠNG SỰ"]: row for row in rows}
    assert "Field bị validator loại" in by_name["Person Synthetic Alpha"]["GHI CHÚ"]
    assert "Field bị validator loại" not in by_name["Person Synthetic Beta"]["GHI CHÚ"]

