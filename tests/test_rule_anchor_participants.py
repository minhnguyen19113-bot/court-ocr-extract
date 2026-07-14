from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import segment_pre_content_anchors
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_specific_participant_roles_are_not_collapsed_to_victim() -> None:
    output = _extract(
        [
            "Người bảo vệ quyền và lợi ích hợp pháp của bị hại: Người Synthetic V",
            "Địa chỉ: Vùng Synthetic V; có mặt",
            "Người bào chữa cho bị cáo: Người Synthetic D",
            "Nơi cư trú: Vùng Synthetic D; vắng mặt",
        ]
    )

    assert [item["role"] for item in output["participants"]] == [
        "Người bảo vệ quyền và lợi ích hợp pháp của bị hại",
        "Người bào chữa cho bị cáo",
    ]
    assert [item["full_name"] for item in output["participants"]] == [
        "Người Synthetic V", "Người Synthetic D",
    ]


def test_victim_heading_attaches_to_person_on_next_line() -> None:
    output = _extract(
        [
            "Bị hại:",
            "Người Synthetic P, sinh năm 1991",
            "Địa chỉ: Vùng Synthetic P",
            "Quan hệ: Vai trò Synthetic",
        ]
    )

    participant = output["participants"][0]
    assert participant["role"] == "Bị hại"
    assert participant["full_name"] == "Người Synthetic P"
    assert participant["address"] == "Vùng Synthetic P"
    assert participant["relationship_or_note"] == "Vai trò Synthetic"


def test_related_party_heading_applies_to_numbered_people() -> None:
    output = _extract(
        [
            "Người có quyền lợi, nghĩa vụ liên quan:",
            "1. Người Synthetic R1, sinh năm 1988",
            "Địa chỉ: Vùng Synthetic R1",
            "2. Người Synthetic R2, sinh năm 1989",
            "Cùng địa chỉ: Vùng Synthetic R1",
        ]
    )

    assert len(output["participants"]) == 2
    assert {item["role"] for item in output["participants"]} == {
        "Người có quyền lợi, nghĩa vụ liên quan"
    }
    assert [item["full_name"] for item in output["participants"]] == [
        "Người Synthetic R1", "Người Synthetic R2",
    ]


def _extract(participant_lines: list[str]) -> dict:
    segment = _segment(
        ["Bản án số: 01/2025/HS-ST", "Đối với bị cáo:", "Người Synthetic A, sinh năm 1990"]
        + participant_lines
    )
    return extract_rule_anchor_output(segment_pre_content_anchors(segment, case_id="synthetic"))
