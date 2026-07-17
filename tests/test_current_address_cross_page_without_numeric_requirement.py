from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_cross_page_address_continuation_can_start_with_text() -> None:
    block = {
        "block_id": "defendant_alpha",
        "line_ids": [
            "p006_l0001",
            "p006_l0002",
            "p007_l0001",
            "p007_l0002",
            "p007_l0003",
        ],
        "text": "\n".join(
            [
                "1. Person Synthetic Alpha, sinh năm 1990",
                "Chỗ ở: Nhà Synthetic không số cạnh căn nhà",
                "7",
                "đường Synthetic, phường Synthetic, thành phố Synthetic;",
                "Nghề nghiệp: Nhân viên synthetic",
            ]
        ),
    }

    result = parse_defendant_block(block)

    assert result["current_address"] == (
        "Nhà Synthetic không số cạnh căn nhà "
        "đường Synthetic, phường Synthetic, thành phố Synthetic"
    )
    assert result["current_address_evidence_line_ids"] == [
        "p006_l0002",
        "p007_l0002",
    ]
