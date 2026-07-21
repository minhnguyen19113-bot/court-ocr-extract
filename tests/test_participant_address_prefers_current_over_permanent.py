from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_participant_block


def test_participant_address_prefers_current_over_permanent() -> None:
    participant = parse_participant_block(
        {
            "block_id": "participant_001",
            "role_hint": "Bị hại",
            "line_ids": ["p001_l0001", "p001_l0002", "p001_l0003"],
            "text": "Người Synthetic A\nThường trú: Vùng Synthetic A\nNơi ở hiện nay: Vùng Synthetic B",
        }
    )

    assert participant["address"] == "Vùng Synthetic B"
