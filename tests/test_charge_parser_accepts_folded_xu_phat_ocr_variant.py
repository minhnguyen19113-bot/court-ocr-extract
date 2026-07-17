from __future__ import annotations

from court_ocr_extract.charge_parser import (
    iter_verdict_blocks,
    parse_verdict_candidate,
)


def test_folded_start_accepts_xu_phat_ocr_variant() -> None:
    blocks = iter_verdict_blocks(
        [
            {
                "line_id": "p004_l0001",
                "page_number": 4,
                "text": (
                    "4.1. Xử phát bị cáo Person Synthetic Alpha 18 tháng tù "
                    "về tội “Charge Synthetic Alpha”."
                ),
            }
        ]
    )

    parsed = parse_verdict_candidate(
        blocks[0],
        [
            {"entity_id": "defendant_alpha", "full_name": "Person Synthetic Alpha"}
        ],
    )

    assert parsed.valid is True
    assert parsed.normalized_charge == "Charge Synthetic Alpha"
    assert parsed.defendant_entity_ids == ["defendant_alpha"]
    assert parsed.match_method.startswith("sentence_for_charge_ve_toi_quoted")
