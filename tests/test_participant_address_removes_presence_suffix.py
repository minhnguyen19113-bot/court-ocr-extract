from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_participant_block


def test_participant_address_removes_presence_suffix() -> None:
    participant = parse_participant_block(
        {
            "block_id": "participant_001",
            "role_hint": "Bị hại",
            "line_ids": ["p001_l0001"],
            "text": "Người Synthetic A; Địa chỉ: Vùng Synthetic B (vắng mặt)",
        }
    )

    assert participant["address"] == "Vùng Synthetic B"
    assert participant["presence_status"] == "Vắng mặt"
