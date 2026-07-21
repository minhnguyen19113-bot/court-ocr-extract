from __future__ import annotations

import pytest

from court_ocr_extract.extractors.rule_anchor_extractor import parse_participant_block


@pytest.mark.parametrize(
    "suffix",
    [
        "(vắng mặt).",
        "( vắng mặt).",
        "(vắng mặt ).",
        "(  vắng mặt  ).",
        "(có mặt).",
        "(có đơn xin vắng mặt).",
    ],
)
def test_participant_address_strips_spaced_presence_suffix_with_period(
    suffix: str,
) -> None:
    participant = parse_participant_block(
        {
            "block_id": "participant_001",
            "role_hint": "Bị hại",
            "line_ids": ["p001_l0001"],
            "text": f"Person Synthetic Alpha; Địa chỉ: Vùng Synthetic A {suffix}",
        }
    )

    assert participant["address"] == "Vùng Synthetic A"
    assert participant["presence_status"] in {"Có mặt", "Vắng mặt", "Có đơn xin vắng mặt"}


def test_participant_address_keeps_non_presence_parenthetical_with_period() -> None:
    participant = parse_participant_block(
        {
            "block_id": "participant_001",
            "role_hint": "Bị hại",
            "line_ids": ["p001_l0001"],
            "text": "Person Synthetic Alpha; Địa chỉ: Vùng Synthetic A (nay là Vùng Synthetic B).",
        }
    )

    assert participant["address"] == "Vùng Synthetic A (nay là Vùng Synthetic B)"
