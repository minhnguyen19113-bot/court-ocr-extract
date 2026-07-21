from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_defendant_address_prefers_noi_o_over_permanent_address() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": [f"p001_l{index:04d}" for index in range(1, 5)],
            "text": "\n".join(
                [
                    "Person Synthetic Alpha, sinh năm 1990",
                    "Hộ khẩu thường trú: Vùng Synthetic Permanent;",
                    "Nơi ở: Vùng Synthetic Current;",
                    "Nghề nghiệp: Kiểm thử synthetic",
                ]
            ),
        }
    )

    assert defendant["permanent_address"] == "Vùng Synthetic Permanent"
    assert defendant["current_address"] == "Vùng Synthetic Current"
