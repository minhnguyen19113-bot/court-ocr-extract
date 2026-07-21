from __future__ import annotations

from court_ocr_extract.charge_parser import parse_explicit_decision_charges
from court_ocr_extract.source_region_policy import DECISION_TAIL


def test_charge_parser_accepts_tuyen_bo_bi_cao() -> None:
    output = parse_explicit_decision_charges(
        [
            {
                "line_id": "p009_l0001",
                "source_region": DECISION_TAIL,
                "text": "Tuyên bố bị cáo Người Synthetic A về tội \"Charge Synthetic Alpha\"",
            }
        ],
        defendants=[{"entity_id": "defendant_001", "full_name": "Người Synthetic A"}],
    )

    assert output["case_charges"] == ["Charge Synthetic Alpha"]
    assert output["defendant_charge_map"] == {"defendant_001": ["Charge Synthetic Alpha"]}
