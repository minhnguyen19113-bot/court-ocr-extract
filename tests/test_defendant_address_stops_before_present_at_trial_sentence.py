from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_defendant_address_stops_before_present_at_trial_sentence() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": [f"p001_l{index:04d}" for index in range(1, 6)],
            "text": "\n".join(
                [
                    "Person Synthetic Alpha, sinh năm 1990",
                    "Hộ khẩu thường trú:",
                    "Vùng Synthetic Permanent;",
                    "Nơi ở: Vùng Synthetic Current;",
                    "Bị cáo có mặt tại phiên tòa.",
                ]
            ),
        }
    )

    assert defendant["current_address"] == "Vùng Synthetic Current"
    assert defendant["presence_status"] == "Có mặt"
