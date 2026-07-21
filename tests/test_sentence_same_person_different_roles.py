from court_ocr_extract.final_excel_builder import build_final_excel_rows
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_sentence_same_person_different_roles() -> None:
    result = {
        "case_id": "synthetic_case",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [
            {
                "entity_id": "person_alpha",
                "source_block_id": "person_alpha",
                "full_name": "Person Synthetic Alpha",
            }
        ],
        "participants": [
            {
                "entity_id": "person_alpha",
                "role": "Bị hại",
                "full_name": "Person Synthetic Alpha",
            }
        ],
        "defendant_sentence_map": {
            "person_alpha": {
                "primary_penalty_text": "2 năm tù",
                "source_region": DECISION_TAIL,
            }
        },
    }

    rows = build_final_excel_rows(result)

    assert len(rows) == 2
    by_role = {row["TƯ CÁCH TỐ TỤNG"]: row for row in rows}
    assert by_role["Bị cáo"]["HÌNH PHẠT"] == "2 năm tù"
    assert by_role["Bị hại"]["HÌNH PHẠT"] == ""
