from __future__ import annotations

import pytest

from court_ocr_extract.charge_parser import parse_explicit_decision_charges


@pytest.mark.parametrize(
    "text",
    [
        "Tuyên bố trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa",
        "Tuyên trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa",
        "Trả tự do cho bị cáo Person Synthetic Alpha tại phiên tòa",
        "Person Synthetic Alpha không bị tạm giam về tội phạm khác.",
        "Person Synthetic Alpha không bị tạm giữ về tội phạm khác.",
    ],
)
def test_tuyen_bo_tra_tu_do_is_not_a_verdict_charge_candidate(text: str) -> None:
    output = parse_explicit_decision_charges(text)

    assert output["case_charges"] == []
    assert output["verdict_candidate_count"] == 0
    assert output["parsed_charge_count"] == 0
    assert "procedural_verdict_candidate_rejected" in output["warnings"]
