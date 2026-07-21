from __future__ import annotations

import pytest

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


@pytest.mark.parametrize("intro", ["Đối với bị cáo:", "Đổi với bị cáo:"])
def test_defendant_intro_uses_folded_text(intro: str) -> None:
    anchor = segment_pre_content_anchors(
        _segment([intro, "Người Synthetic A, sinh năm 1990", "Bị hại: Người Synthetic B"]),
        case_id="synthetic_case",
    )

    output = extract_rule_anchor_output(anchor)

    assert anchor["defendant_region"]["intro_found"] is True
    assert output["defendants"][0]["full_name"] == "Người Synthetic A"
