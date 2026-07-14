from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import segment_pre_content_anchors
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_hierarchical_numbering_and_inline_roles_create_four_participants() -> None:
    participant_lines = [
        "7.1. Bị hại Người Synthetic A-có mặt",
        "Địa chỉ: Khu Synthetic A",
        "Người giám hộ: Bà Synthetic B (là người thân)-có mặt",
        "Địa chỉ: Khu Synthetic B",
        (
            "7.2. Người bảo vệ quyền và lợi ích hợp pháp của bị hại: Ông Synthetic C, "
            "Luật sư Văn phòng Luật sư Synthetic-thuộc Đoàn Synthetic-có mặt"
        ),
        "Địa chỉ: Khu Synthetic C",
        "7.3. Bị hại Người Synthetic D-có mặt",
        "Địa chỉ: Khu Synthetic D",
    ]
    segment = _segment(
        [
            "Bản án số: 01/2025/HS-ST",
            "Đối với bị cáo:",
            "Người Synthetic Defendant, sinh năm 1990",
            *participant_lines,
        ]
    )

    anchor = segment_pre_content_anchors(segment, case_id="synthetic")
    output = extract_rule_anchor_output(anchor)

    assert len(anchor["participant_blocks"]) == 4
    assert [item["role"] for item in output["participants"]] == [
        "Bị hại",
        "Người giám hộ",
        "Người bảo vệ quyền và lợi ích hợp pháp của bị hại",
        "Bị hại",
    ]
    assert [item["full_name"] for item in output["participants"]] == [
        "Người Synthetic A",
        "Bà Synthetic B",
        "Ông Synthetic C",
        "Người Synthetic D",
    ]
    assert all(item["presence_status"] == "Có mặt" for item in output["participants"])
    assert output["participants"][1]["relationship_or_note"] == "là người thân"
    assert "Luật sư Văn phòng Luật sư Synthetic" in (
        output["participants"][2]["relationship_or_note"] or ""
    )
    assert all(len(block["line_ids"]) == 2 for block in anchor["participant_blocks"])

