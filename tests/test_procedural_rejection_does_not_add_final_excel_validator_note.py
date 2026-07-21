from court_ocr_extract.final_excel_builder import build_final_excel_rows


def test_procedural_rejection_does_not_add_final_excel_validator_note() -> None:
    rows = build_final_excel_rows({
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [{"full_name": "Person Synthetic Alpha"}],
        "warnings": ["procedural_verdict_candidate_rejected"],
    })
    assert "Field bị validator loại" not in rows[0]["GHI CHÚ"]

