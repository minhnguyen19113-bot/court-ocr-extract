from court_ocr_extract.final_excel_builder import build_final_excel_rows
from tests.sentence_test_support import parse_sentence


def test_cross_source_name_disagreement_does_not_change_final_name() -> None:
    sentence_output = parse_sentence("Xử phạt bị cáo Person Synthetic Alpho 09 tháng tù về tội “Charge Synthetic”.")
    rows = build_final_excel_rows({
        "case_id": "case_synthetic_name",
        "document_type": "judgment_criminal_first_instance",
        "metadata": {},
        "trial_panel": {},
        "defendants": [{"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}],
        "decision_tail_status": "parsed",
        "defendant_sentence_map": sentence_output["defendant_sentence_map"],
    })
    assert rows[0]["HỌ TÊN ĐƯƠNG SỰ"] == "Person Synthetic Alpha"

