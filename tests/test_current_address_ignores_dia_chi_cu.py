from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_current_address_ignores_dia_chi_cu() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": ["p001_l0001", "p001_l0002"],
            "text": (
                "Person Synthetic Alpha, sinh năm 1990\n"
                "Địa chỉ cũ: Vùng Synthetic Old"
            ),
        }
    )

    assert defendant["current_address"] is None
    assert defendant["current_address_evidence_line_ids"] == []
