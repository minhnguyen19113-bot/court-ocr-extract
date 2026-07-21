from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_participant_block


def test_participant_name_strips_leading_honorific() -> None:
    participant = parse_participant_block(
        {
            "block_id": "participant_001",
            "role_hint": "Bị hại",
            "line_ids": ["p001_l0001"],
            "text": "Bị hại: Bà Người Synthetic A",
        }
    )

    assert participant["full_name"] == "Người Synthetic A"
