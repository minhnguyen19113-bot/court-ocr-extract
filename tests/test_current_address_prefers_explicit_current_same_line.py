from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_current_address_prefers_explicit_current_on_same_line() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": ["p001_l0001"],
            "text": (
                "Person Synthetic Alpha, sinh năm 1990; "
                "Địa chỉ cũ: Vùng Synthetic Old; "
                "Nơi ở hiện nay: Vùng Synthetic Current; "
                "Nghề nghiệp: Kiểm thử synthetic"
            ),
        }
    )

    assert defendant["current_address"] == "Vùng Synthetic Current"
    assert defendant["current_address_evidence_line_ids"] == ["p001_l0001"]


def test_current_address_uses_latest_candidate_at_same_priority() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": ["p001_l0001", "p001_l0002", "p001_l0003"],
            "text": "\n".join(
                [
                    "Person Synthetic Alpha, sinh năm 1990",
                    "Nơi ở hiện nay: Vùng Synthetic Earlier",
                    "Nơi ở hiện tại: Vùng Synthetic Latest",
                ]
            ),
        }
    )

    assert defendant["current_address"] == "Vùng Synthetic Latest"
    assert defendant["current_address_evidence_line_ids"] == ["p001_l0003"]
