from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_quoted_charge_continues_across_page_boundary() -> None:
    output = parse_explicit_decision_charges(
        [
            _line(7, 1, "Xử phạt bị cáo Person Synthetic Alpha về tội “Trộm cấp"),
            _line(7, 2, "8"),
            _line(8, 1, "tài sản”, theo quy định synthetic."),
        ],
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    evidence = output["charge_evidence"][0]
    assert output["verdict_candidate_count"] == 1
    assert output["parsed_charge_count"] == 1
    assert output["mapped_defendant_count"] == 1
    assert output["unmapped_verdict_count"] == 0
    assert output["invalid_charge_count"] == 0
    assert evidence["raw_charge"] == "Trộm cấp\ntài sản"
    assert evidence["normalized_charge"] == "Trộm cấp tài sản"
    assert evidence["canonical_charge"] == "Trộm cắp tài sản"
    assert evidence["line_ids"] == ["p007_l0001", "p008_l0001"]


def _line(page: int, order: int, text: str) -> dict:
    return {
        "line_id": f"p{page:03d}_l{order:04d}",
        "page_number": page,
        "reading_order": order - 1,
        "source_region": DECISION_TAIL,
        "text": text,
    }
