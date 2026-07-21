from __future__ import annotations

import pytest

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


@pytest.mark.parametrize(
    "presence_line, expected",
    [
        ("Bị cáo vắng mặt tại phiên tòa.", "Vắng mặt"),
        ("Bị cáo có đơn xin vắng mặt", "Có đơn xin vắng mặt"),
        ("Có mặt tại phiên tòa", "Có mặt"),
        ("Vắng mặt tại phiên tòa", "Vắng mặt"),
    ],
)
def test_defendant_address_stops_before_absent_at_trial_sentence(
    presence_line: str,
    expected: str,
) -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": ["p001_l0001", "p001_l0002", "p001_l0003"],
            "text": "\n".join(
                [
                    "Person Synthetic Alpha, sinh năm 1990",
                    "Nơi ở: Vùng Synthetic Current;",
                    presence_line,
                ]
            ),
        }
    )

    assert defendant["current_address"] == "Vùng Synthetic Current"
    assert defendant["presence_status"] == expected
