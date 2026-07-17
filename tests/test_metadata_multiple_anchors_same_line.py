from __future__ import annotations

from tests.test_rule_anchor_metadata import _extract


def test_all_metadata_anchors_are_extracted_from_one_ocr_line() -> None:
    output = _extract(
        [
            "Bản án số: 903/2099/HS-ST",
            (
                "thụ lý số 904/2099/TLST-HS ngày 05 tháng 2 năm 2099; "
                "Quyết định đưa vụ án ra xét xử số 905/2099/QĐXXST-HS "
                "ngày 20 tháng 2 năm 2099; Quyết định hoãn phiên tòa số "
                "906/2099/HSST-QĐ ngày 25 tháng 2 năm 2099"
            ),
            "Đối với bị cáo:",
            "Người Synthetic A, sinh năm 1990",
        ]
    )

    metadata = output["metadata"]
    assert metadata["case_acceptance_number"] == "904/2099/TLST-HS"
    assert metadata["case_acceptance_date"] == "05/02/2099"
    assert metadata["trial_decision_number"] == "905/2099/QĐXXST-HS"
    assert metadata["postponement_decision_number"] == "906/2099/HSST-QĐ"
