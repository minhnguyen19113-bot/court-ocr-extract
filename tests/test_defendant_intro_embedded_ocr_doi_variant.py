from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_embedded_ocr_doi_variant_starts_defendant_region() -> None:
    anchor = segment_pre_content_anchors(
        _segment(
            [
                "Quyết định synthetic: Đổi với các bị cáo:",
                "1. Người Synthetic A; giới tính: Nam; sinh năm 1990",
                "Bị hại: Người Synthetic B",
            ]
        ),
        case_id="synthetic_case",
    )

    output = extract_rule_anchor_output(anchor)

    assert anchor["defendant_region"]["intro_line_id"] == "p001_l0001"
    assert output["defendants"][0]["full_name"] == "Người Synthetic A"
