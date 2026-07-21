from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_numbered_defendant_with_semicolon_gender_and_birth_is_detected() -> None:
    output = extract_rule_anchor_output(
        segment_pre_content_anchors(
            _segment(
                [
                    "Đối với bị cáo:",
                    "1. Người Synthetic A; giới tính: Nam; Sinh ngày: 01/01/1990",
                    "Bị hại: Người Synthetic B",
                ]
            ),
            case_id="synthetic_case",
        )
    )

    assert output["defendants"][0]["full_name"] == "Người Synthetic A"
    assert output["defendants"][0]["birth_date_or_year"] == "01/01/1990"
