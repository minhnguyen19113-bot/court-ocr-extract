from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_multiline_address_overrides_legacy_single_line_value() -> None:
    block = {
        "block_id": "defendant_alpha",
        "line_ids": [f"p003_l{index:04d}" for index in range(1, 5)],
        "text": "\n".join(
            [
                "1. Person Synthetic Alpha, sinh năm 1990",
                "Chỗ ở: Nhà Synthetic không số cạnh căn nhà",
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
        "p003_l0002",
        "p003_l0003",
    ]
    assert "Nghề nghiệp" not in result["current_address"]
