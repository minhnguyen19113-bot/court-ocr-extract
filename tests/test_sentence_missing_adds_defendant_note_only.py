from court_ocr_extract.final_excel_builder import build_final_excel_rows


def test_sentence_missing_adds_defendant_note_only() -> None:
    rows = build_final_excel_rows(
        {
            "case_id": "synthetic_case",
            "document_type": "judgment_criminal_first_instance",
            "metadata": {},
            "trial_panel": {},
            "decision_tail_status": "parsed",
            "defendants": [
                {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
            ],
            "participants": [
                {"entity_id": "victim_alpha", "role": "Bị hại", "full_name": "Victim Synthetic Alpha"}
            ],
            "defendant_sentence_map": {},
        }
    )

    by_role = {row["TƯ CÁCH TỐ TỤNG"]: row for row in rows}
    assert by_role["Bị cáo"]["HÌNH PHẠT"] == ""
    assert "Chưa trích xuất chắc hình phạt từ phần Quyết định" in by_role["Bị cáo"]["GHI CHÚ"]
    assert "hình phạt" not in by_role["Bị hại"]["GHI CHÚ"].casefold()


def test_heading_not_found_blocks_sentence_map() -> None:
    rows = build_final_excel_rows(
        {
            "case_id": "synthetic_case",
            "document_type": "judgment_criminal_first_instance",
            "metadata": {},
            "trial_panel": {},
            "decision_tail_status": "heading_not_found",
            "defendants": [
                {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
            ],
            "defendant_sentence_map": {
                "defendant_alpha": {
                    "primary_penalty_text": "2 năm tù",
                    "source_region": "decision_tail",
                }
            },
        }
    )

    assert rows[0]["HÌNH PHẠT"] == ""
    assert "Không có nguồn để trích xuất hình phạt" in rows[0]["GHI CHÚ"]
