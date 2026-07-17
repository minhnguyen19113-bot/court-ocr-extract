from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_defendant_address_continues_across_page_and_stops_at_next_field() -> None:
    lines = [
        "1. Person Synthetic Alpha, sinh năm 1990",
        "Nơi ở hiện nay: Segment Synthetic One",
        "12 Route Synthetic",
        "8",
        "Ward Synthetic Continuation",
        "Nghề nghiệp: Occupation Synthetic",
        "Tiền án: Không",
    ]
    line_ids = [
        "p001_l0001",
        "p001_l0002",
        "p001_l0003",
        "p002_l0001",
        "p002_l0002",
        "p002_l0003",
        "p002_l0004",
    ]
    result = parse_defendant_block(
        {
            "block_id": "defendant_alpha",
            "text": "\n".join(lines),
            "line_ids": line_ids,
            "split_reason": "defendant_label",
        }
    )

    assert result["current_address"] == (
        "Segment Synthetic One 12 Route Synthetic Ward Synthetic Continuation"
    )
    assert "Occupation Synthetic" not in result["current_address"]
    assert " 8 " not in f" {result['current_address']} "
    assert "p001_l0002" in result["evidence_line_ids"]
    assert "p002_l0002" in result["evidence_line_ids"]
