from __future__ import annotations

import pytest

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


@pytest.mark.parametrize(
    "charge",
    [
        "phạm khác",
        "tội phạm khác",
        "về tội phạm khác",
        "phạm tội khác",
        "một tội phạm khác",
    ],
)
def test_toi_pham_khac_is_rejected_before_canonicalization(charge: str) -> None:
    output = parse_explicit_decision_charges(
        f"Tuyên bố bị cáo Person Synthetic Alpha phạm tội “{charge}”.",
        defendants=[
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert output["case_charges"] == []
    assert output["invalid_charge_count"] == 1
    assert "invalid_charge_candidate_rejected" in output["warnings"]
    assert "procedural_charge_candidate_rejected" in output["warnings"]
