from __future__ import annotations

from court_ocr_extract.extractors.rule_anchor_extractor import parse_defendant_block


def test_spouse_children_detention_and_address_continuation_are_normalized() -> None:
    block = {
        "block_id": "defendant_001",
        "line_ids": [f"p001_l{index:04d}" for index in range(1, 7)],
        "text": "\n".join(
            [
                "1. Người Synthetic A, sinh năm 1990",
                "Vợ con: có vợ, 01 con sinh năm 2024.",
                "Chỗ ở: hiện tại: Nhà Synthetic cạnh nhà",
                "số 275/36 Đường Synthetic, Phường Synthetic",
                "Nghề nghiệp: Kiểm thử",
                "tam giam từ ngày 01/01/2025",
            ]
        ),
    }

    defendant = parse_defendant_block(block)

    assert defendant["spouse"] == "có vợ"
    assert defendant["children"] == "01 con sinh năm 2024"
    assert defendant["detention_status"] == "tạm giam từ ngày 01/01/2025"
    assert defendant["current_address"] == (
        "Nhà Synthetic cạnh nhà số 275/36 Đường Synthetic, Phường Synthetic"
    )
    assert not defendant["current_address"].lower().startswith("hiện tại:")

