from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    segment_pre_content_anchors,
)
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_guardian_block_with_multiple_honorific_names_splits_safely() -> None:
    output = _extract(
        "Người giám hộ của bị cáo: Ông Synthetic A, bà Synthetic B (cha mẹ synthetic)"
    )

    assert [item["full_name"] for item in output["participants"]] == [
        "Ông Synthetic A",
        "bà Synthetic B",
    ]
    assert all(item["role"] == "Người giám hộ của bị cáo" for item in output["participants"])
    assert all(
        item["relationship_or_note"] == "cha mẹ synthetic"
        for item in output["participants"]
    )
    assert output["participants"][0]["evidence_line_ids"] == (
        output["participants"][1]["evidence_line_ids"]
    )


def test_multi_person_split_is_blocked_when_tail_is_an_address() -> None:
    output = _extract(
        "Người giám hộ: Ông Synthetic A, bà Synthetic B, địa chỉ Vùng Synthetic"
    )

    assert len(output["participants"]) == 1


def _extract(participant_line: str) -> dict:
    segment = _segment(
        [
            "Bản án số: 910/2099/HS-ST",
            "Đối với bị cáo:",
            "Người Synthetic D, sinh năm 1990",
            participant_line,
        ]
    )
    return extract_rule_anchor_output(
        segment_pre_content_anchors(segment, case_id="synthetic_case")
    )
