from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


def test_statute_behavior_and_crime_keyword_without_verdict_are_ignored() -> None:
    output = parse_explicit_decision_charges(
        [
            {"text": "Căn cứ Điều synthetic về Charge Synthetic Alpha."},
            {"text": "Hành vi synthetic có dấu hiệu tội phạm synthetic."},
            {"text": "Cáo trạng synthetic đề nghị áp dụng điều luật synthetic."},
        ],
        defendants=[
            {"entity_id": "defendant_001", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output == {
        "case_charges": [],
        "defendant_charge_map": {},
        "charge_evidence": [],
        "warnings": [],
    }

