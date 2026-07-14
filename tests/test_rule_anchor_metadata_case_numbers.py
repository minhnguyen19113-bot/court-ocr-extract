from __future__ import annotations

from tests.test_rule_anchor_metadata import _extract


def test_case_numbers_are_single_tokens_even_after_long_header_region() -> None:
    texts = ["Bản án số: 01/2025/HS-ST"]
    texts.extend(f"Dòng header synthetic {index}" for index in range(105))
    texts.extend(
        [
            "thụ lý số 118/2025/TLST-HS ngày 09 tháng 4 năm 2025",
            "Quyết định đưa vụ án ra xét xử số 167/2025/QĐXXST-HS theo thủ tục synthetic",
            "Quyết định hoãn phiên tòa số 43/2025/HSST-QĐ ngày 29 tháng 5 năm 2025",
            "Đối với bị cáo:",
            "Người Synthetic A, sinh năm 1990",
        ]
    )

    metadata = _extract(texts)["metadata"]

    assert metadata["case_acceptance_number"] == "118/2025/TLST-HS"
    assert metadata["trial_decision_number"] == "167/2025/QĐXXST-HS"
    assert metadata["postponement_decision_number"] == "43/2025/HSST-QĐ"
    assert "ngày" not in metadata["case_acceptance_number"]
    assert "theo" not in metadata["trial_decision_number"]

