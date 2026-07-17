from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import (
    extract_rule_anchor_output,
    parse_defendant_block,
)
from tests.test_rule_anchor_metadata import _segment


def test_numbered_trial_panel_members_never_become_defendants() -> None:
    segment = _segment(
        [
            "THÀNH PHẦN HỘI ĐỒNG XÉT XỬ",
            "Hội thẩm nhân dân:",
            "1. Ông Hội Đồng Synthetic A",
            "2. Bà Hội Đồng Synthetic B",
            "thụ lý số 900/2099/TLST-HS ngày 01 tháng 2 năm 2099",
            "Đối với các bị cáo:",
            "1. Người Bị Cáo Synthetic, sinh năm 1990",
            "Nơi ở hiện nay: Vùng Synthetic",
            "Bị hại: Người Bị Hại Synthetic",
        ]
    )

    anchor = segment_pre_content_anchors(segment, case_id="synthetic_case")
    output = extract_rule_anchor_output(anchor)
    panel_ids = {line["line_id"] for line in anchor["trial_panel_lines"]}
    defendant_ids = {
        line_id
        for block in anchor["defendant_blocks"]
        for line_id in block["line_ids"]
    }

    assert panel_ids.isdisjoint(defendant_ids)
    assert [item["full_name"] for item in output["defendants"]] == [
        "Người Bị Cáo Synthetic"
    ]
    assert all("Hội Đồng Synthetic" not in item["full_name"] for item in output["defendants"])


def test_numbered_panel_without_defendant_intro_creates_no_defendant_block() -> None:
    anchor = segment_pre_content_anchors(
        _segment(["Hội thẩm nhân dân:", "1. Ông Synthetic A", "2. Bà Synthetic B"]),
        case_id="synthetic_case",
    )

    assert anchor["defendant_blocks"] == []
    assert anchor["defendant_region"]["intro_found"] is False


def test_defendant_validator_rejects_pure_name_without_identity_profile() -> None:
    result = parse_defendant_block(
        {
            "block_id": "defendant_synthetic",
            "line_ids": ["p001_l0001"],
            "text": "1. Ông Synthetic A",
            "split_reason": "numbered_person_with_profile_followup",
        }
    )

    assert result["entity_valid"] is False
    assert "defendant_identity_profile_missing" in result["warnings"]
