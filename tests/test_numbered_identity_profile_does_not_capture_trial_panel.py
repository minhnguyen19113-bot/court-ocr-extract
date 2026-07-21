from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_numbered_identity_profile_does_not_capture_trial_panel() -> None:
    output = extract_rule_anchor_output(
        segment_pre_content_anchors(
            _segment(
                [
                    "Thành phần Hội đồng xét xử:",
                    "1. Người Synthetic Panel; giới tính: Nam; nghề nghiệp: Hội thẩm",
                    "Đối với bị cáo:",
                    "1. Người Synthetic A; giới tính: Nam; sinh năm 1990",
                    "Bị hại: Người Synthetic B",
                ]
            ),
            case_id="synthetic_case",
        )
    )

    assert [item["full_name"] for item in output["defendants"]] == ["Người Synthetic A"]
