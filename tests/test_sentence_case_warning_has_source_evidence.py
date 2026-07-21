from court_ocr_extract.sentence_parser import parse_defendant_sentences
from tests.sentence_test_support import DEFENDANTS, line


def test_sentence_case_warning_has_source_evidence() -> None:
    output = parse_defendant_sentences(
        [
            line(8, 1, "Xử phạt bị cáo Person Synthetic Unknown 09 tháng tù về tội “Charge Synthetic”."),
            line(8, 2, "Thời hạn tù tính từ ngày chưa xác định."),
        ],
        defendants=DEFENDANTS[:1],
        case_id="case_synthetic_unmapped",
    )
    warning = next(
        item for item in output["sentence_warnings"]
        if item["warning"] == "sentence_start_anchor_unparsed"
    )
    assert warning["scope"] == "case"
    assert warning["defendant_entity_id"] == ""
    assert warning["page_number"] == 8
    assert warning["line_ids"] == ["p008_l0002"]
    assert warning["raw_text"] == "Thời hạn tù tính từ ngày chưa xác định."

