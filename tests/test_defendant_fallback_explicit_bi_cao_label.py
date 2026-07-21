from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_explicit_bi_cao_label_fallback_requires_identity_profile() -> None:
    anchor = segment_pre_content_anchors(
        _segment(
            [
                "Thành phần Hội đồng xét xử:",
                "Thẩm phán: Người Synthetic Panel",
                "Bị cáo: Người Synthetic A, sinh năm 1990",
                "Bị hại: Người Synthetic B",
            ]
        ),
        case_id="synthetic_case",
    )

    output = extract_rule_anchor_output(anchor)

    assert anchor["defendant_region"]["intro_found"] is True
    assert anchor["defendant_blocks"][0]["split_reason"] == (
        "fallback_explicit_defendant_label"
    )
    assert output["defendants"][0]["full_name"] == "Người Synthetic A"
