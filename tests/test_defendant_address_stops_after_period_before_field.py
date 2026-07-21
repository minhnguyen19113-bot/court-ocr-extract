from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_defendant_address_stops_after_period_before_next_field() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": ["p001_l0001"],
            "text": (
                "Người Synthetic A, sinh năm 1990. Nơi ở hiện nay: "
                "Vùng Synthetic (địa chỉ cũ). Nghề nghiệp: Kiểm thử synthetic."
            ),
        }
    )

    assert defendant["current_address"] == "Vùng Synthetic (địa chỉ cũ)"
    assert "Nghề nghiệp" not in defendant["current_address"]
