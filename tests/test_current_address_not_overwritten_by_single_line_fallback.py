from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_inline_label_multiline_address_is_not_replaced_by_short_fallback() -> None:
    block = {
        "block_id": "defendant_alpha",
        "line_ids": ["p002_l0001", "p002_l0002", "p002_l0003"],
        "text": "\n".join(
            [
                "1. Person Synthetic Alpha, sinh năm 1990; Chỗ ở: Vùng Synthetic đầu",
                "phường Synthetic, quận Synthetic, thành phố Synthetic",
                "Trình độ văn hóa: Synthetic",
            ]
        ),
    }

    result = parse_defendant_block(block)

    assert result["current_address"] == (
        "Vùng Synthetic đầu phường Synthetic, quận Synthetic, thành phố Synthetic"
    )
    assert "Trình độ" not in result["current_address"]
