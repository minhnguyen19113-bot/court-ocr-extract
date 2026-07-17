from __future__ import annotations

import pytest

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


@pytest.mark.parametrize("intro", ["Đối với các bị cáo:", "Đồi với các bị cáo:"])
def test_embedded_intro_starts_defendant_region_on_following_line(intro: str) -> None:
    segment = _segment(
        [
            "Bản án số: 901/2099/HS-ST",
            "Quyết định đưa vụ án ra xét xử số 902/2099/QĐXXST-HS " + intro,
            "1. Người Synthetic A, sinh năm 1990",
            "Nghề nghiệp: Kiểm thử synthetic",
            "Bị hại: Người Synthetic B",
        ]
    )

    anchor = segment_pre_content_anchors(segment, case_id="synthetic_case")
    output = extract_rule_anchor_output(anchor)

    assert anchor["defendant_region"]["intro_line_id"] == "p001_l0002"
    assert anchor["defendant_region"]["start_line_id"] == "p001_l0003"
    assert anchor["defendant_blocks"][0]["start_line_id"] == "p001_l0003"
    assert output["metadata"]["trial_decision_number"] == "902/2099/QĐXXST-HS"
    assert output["defendants"][0]["full_name"] == "Người Synthetic A"


def test_inline_defendant_requires_strong_identity_evidence() -> None:
    weak = segment_pre_content_anchors(
        _segment(["Đối với bị cáo: Cụm Synthetic Không Đủ Mạnh"]),
        case_id="synthetic_case",
    )
    strong = segment_pre_content_anchors(
        _segment(["Đối với bị cáo: Người Synthetic A, sinh năm 1990"]),
        case_id="synthetic_case",
    )

    assert weak["defendant_blocks"] == []
    assert weak["rejected_defendant_candidates"][0]["reason"] == (
        "inline_defendant_without_strong_identity_evidence"
    )
    assert strong["defendant_blocks"][0]["start_line_id"] == "p001_l0001"
