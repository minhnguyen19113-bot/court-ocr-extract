from __future__ import annotations

from court_ocr_extract.extractors.rule_based_pre_content_extractor import extract_pre_content_rules


def test_extracts_metadata_panel_multiple_defendants_and_participants() -> None:
    segment = _segment([
        "TÒA ÁN NHÂN DÂN THÀNH PHỐ HỒ CHÍ MINH",
        "Bản án số: 01/2026/HS-ST",
        "Ngày: 10/01/2026",
        "Chủ tọa phiên tòa: Nguyễn Chủ Tọa",
        "Các Hội thẩm nhân dân:",
        "1. Trần Hội Thẩm",
        "2. Lê Hội Thẩm",
        "Thư ký phiên tòa: Phạm Thư Ký",
        "Đối với bị cáo:",
        "1. Họ và tên: Nguyễn Văn A",
        "Sinh năm: 1990",
        "Nơi thường trú: Địa chỉ A",
        "2. Họ và tên: Trần Văn B",
        "Sinh năm: 1992",
        "Bị hại:",
        "1. Lê Văn C, có mặt",
    ])

    output = extract_pre_content_rules(segment)

    assert output["metadata"]["judgment_number"] == "01/2026/HS-ST"
    assert output["trial_panel"]["presiding_judge"] == "Nguyễn Chủ Tọa"
    assert len(output["trial_panel"]["jurors"]) == 2
    assert [item["full_name"] for item in output["defendants"]] == ["Nguyễn Văn A", "Trần Văn B"]
    assert output["defendants"][1]["evidence_line_ids"]
    assert output["participants"][0]["role"] == "Bị hại"


def test_correction_notice_uses_separate_light_schema() -> None:
    segment = _segment([
        "THÔNG BÁO SỐ: 02/2026/TB-TA",
        "Ngày 11/01/2026",
        "SỬA CHỮA BỔ SUNG BẢN ÁN",
        "Bản án số: 01/2026/HS-ST",
        "Từ: nội dung cũ",
        "Thành: nội dung mới",
    ], document_type="correction_notice")

    output = extract_pre_content_rules(segment)

    assert output["document_type"] == "correction_notice"
    assert output["notice"]["referenced_judgment_number"] == "01/2026/HS-ST"
    assert "correction_notice_excluded_from_judgment_benchmark" in output["warnings"]


def _segment(texts, document_type="judgment_criminal_first_instance"):
    return {
        "document_type": document_type,
        "pre_content_text": "\n".join(texts),
        "pre_content_lines": [
            {"line_id": f"p001_l{index:04d}", "page_number": 1, "text": text}
            for index, text in enumerate(texts, start=1)
        ],
        "warnings": [],
    }
