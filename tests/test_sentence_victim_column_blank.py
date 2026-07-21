from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_sentence_victim_column_blank() -> None:
    rows = build_final_excel_rows(
        {
            "case_id": "synthetic_case",
            "document_type": "judgment_criminal_first_instance",
            "metadata": {},
            "trial_panel": {},
            "defendants": [],
            "participants": [
                {
                    "entity_id": "victim_alpha",
                    "role": "Bị hại",
                    "full_name": "Victim Synthetic Alpha",
                }
            ],
            "defendant_sentence_map": {
                "victim_alpha": {
                    "primary_penalty_text": "3 năm tù",
                    "source_region": DECISION_TAIL,
                }
            },
        }
    )

    assert rows[0]["HÌNH PHẠT"] == ""
    assert "hình phạt" not in rows[0]["GHI CHÚ"].casefold()
