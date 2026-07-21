from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_current_address_without_any_residence_label_stays_empty() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": ["p001_l0001"],
            "text": "Person Synthetic Alpha, sinh năm 1990; Nghề nghiệp: Kiểm thử",
        }
    )

    assert defendant["current_address"] is None
    assert defendant["current_address_evidence_line_ids"] == []
