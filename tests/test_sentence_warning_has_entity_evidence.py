from court_ocr_extract.sentence_parser import parse_defendant_sentences
from tests.sentence_test_support import DEFENDANTS, line


def test_sentence_warning_has_entity_evidence() -> None:
    output = parse_defendant_sentences(
        [
            line(8, 1, "Xử phạt bị cáo Person Synthetic Alpha 02 năm tù về tội “Charge Synthetic”, cho hưởng án treo."),
            line(8, 2, "Thời gian thử thách 04 năm, 06..."),
        ],
        defendants=DEFENDANTS[:1],
        case_id="case_synthetic_warning",
    )
    warning = next(
        item for item in output["sentence_warnings"]
        if item["warning"] == "probation_duration_partial"
    )
    assert warning["case_id"] == "case_synthetic_warning"
    assert warning["scope"] == "entity"
    assert warning["defendant_entity_id"] == "defendant_alpha"
    assert warning["defendant_name"] == "Person Synthetic Alpha"
    assert warning["page_number"] == 8
    assert warning["line_ids"] == ["p008_l0001", "p008_l0002"]
    assert "Thời gian thử thách" in warning["raw_text"]
    assert warning["source_region"] == "decision_tail"

