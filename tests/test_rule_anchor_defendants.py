from __future__ import annotations

from court_ocr_extract.extractors.pre_content_anchor_segmenter import segment_pre_content_anchors
from court_ocr_extract.extractors.rule_anchor_extractor import extract_rule_anchor_output
from tests.test_rule_anchor_metadata import _segment


def test_qdxx_is_not_a_defendant_and_single_unnumbered_defendant_is_parsed() -> None:
    segment = _segment(
        [
            "Bản án số: 01/2025/HS-ST",
            "Đối với bị cáo:",
            "Quyết định đưa vụ án ra xét xử số: 02/2025/QĐXX",
            "Người Synthetic A, sinh năm 1990",
            "Nghề nghiệp: Kiểm thử; Quốc tịch: Synthetic",
            "Bị cáo có mặt tại phiên tòa",
            "Bị hại:",
            "Người Synthetic P",
        ]
    )

    anchor = segment_pre_content_anchors(segment, case_id="synthetic")
    output = extract_rule_anchor_output(anchor)

    assert len(anchor["defendant_blocks"]) == 1
    assert output["defendants"][0]["full_name"] == "Người Synthetic A"
    assert "Quyết định" not in output["defendants"][0]["raw_block"]


def test_numbered_defendants_split_and_page_number_is_removed() -> None:
    segment = _segment(
        [
            "Bản án số: 01/2025/HS-ST",
            "Đối với các bị cáo:",
            "1. Người Synthetic A, sinh năm 1990",
            "Nơi ở hiện nay: Vùng Synthetic A",
            "1",
            "2. Họ và tên: Người Synthetic B, sinh ngày 02/02/1992",
            "Tạm giam từ ngày 01/01/2025",
            "2",
            "3. Người Synthetic C Sinh năm 1993",
            "Thường trú: Vùng Synthetic C",
            "Người làm chứng:",
            "Người Synthetic W",
        ]
    )

    anchor = segment_pre_content_anchors(segment, case_id="synthetic")
    output = extract_rule_anchor_output(anchor)

    assert [item["full_name"] for item in output["defendants"]] == [
        "Người Synthetic A", "Người Synthetic B", "Người Synthetic C",
    ]
    assert all("\n1\n" not in f"\n{block['text']}\n" for block in anchor["defendant_blocks"])
    assert all("\n2\n" not in f"\n{block['text']}\n" for block in anchor["defendant_blocks"])
    assert "standalone_page_number_removed_from_defendant_blocks" in anchor["warnings"]
