from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_defendant_address_multiline_noi_o() -> None:
    defendant = parse_defendant_block(
        {
            "block_id": "defendant_001",
            "line_ids": [f"p001_l{index:04d}" for index in range(1, 6)],
            "text": "\n".join(
                [
                    "Person Synthetic Alpha, sinh năm 1990",
                    "Nơi ở:",
                    "Vùng Synthetic One",
                    "Phường Synthetic Two;",
                    "Nghề nghiệp: Kiểm thử synthetic",
                ]
            ),
        }
    )

    assert defendant["current_address"] == "Vùng Synthetic One Phường Synthetic Two"
    assert defendant["current_address_evidence_line_ids"] == [
        "p001_l0002",
        "p001_l0003",
        "p001_l0004",
    ]
