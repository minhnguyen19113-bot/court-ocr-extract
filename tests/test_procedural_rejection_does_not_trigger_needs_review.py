from court_ocr_extract.decision_tail import DecisionTailRecord
from court_ocr_extract.pre_content_ab import _attach_decision_tail_charges
from court_ocr_extract.settings import PipelineSettings
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


def test_procedural_rejection_does_not_trigger_needs_review() -> None:
    output = {
        "case_id": "case_synthetic_procedural",
        "defendants": [{
            "entity_id": "defendant_alpha",
            "full_name": "Person Synthetic Alpha",
            "source_region": FRONT_PRE_CONTENT,
        }],
        "warnings": [],
        "needs_review": False,
    }
    lines = [
        {"line_id": "p008_l0001", "page_number": 8, "source_region": DECISION_TAIL, "text": "Xử phạt bị cáo Person Synthetic Alpha 09 tháng tù về tội “Charge Synthetic”."},
        {"line_id": "p008_l0002", "page_number": 8, "source_region": DECISION_TAIL, "text": "1.2. Tuyên bố trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa."},
    ]
    tail = DecisionTailRecord(
        case_id="case_synthetic_procedural", source_index=1, pdf_hash="synthetic",
        backend="synthetic", pages_total=8, scanned_page_numbers=[8], scan_batches=[[8]],
        heading_found=True, heading_page=8, heading_line_id="p008_l0000",
        heading_text="QUYẾT ĐỊNH", text="\n".join(item["text"] for item in lines), lines=lines,
    )
    _attach_decision_tail_charges(output, tail, settings=PipelineSettings())
    assert "procedural_verdict_candidate_rejected" in output["warnings"]
    assert output["needs_review"] is False
