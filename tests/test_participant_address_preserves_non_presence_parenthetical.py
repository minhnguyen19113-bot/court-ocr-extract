from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_participant_block


def test_participant_address_preserves_non_presence_parenthetical() -> None:
    participant = parse_participant_block(
        {
            "block_id": "participant_001",
            "role_hint": "Bị hại",
            "line_ids": ["p001_l0001"],
            "text": "Person Synthetic Alpha; Địa chỉ: Vùng Synthetic A (nay là Vùng Synthetic B)",
        }
    )

    assert participant["address"] == "Vùng Synthetic A (nay là Vùng Synthetic B)"
