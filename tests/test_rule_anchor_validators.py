from __future__ import annotations

from court_ocr_extract.extractors.pre_content_schema import DEFENDANT_FIELDS
from court_ocr_extract.extractors.pre_content_segmenter import route_document
from court_ocr_extract.extractors.rule_anchor_extractor import validate_defendant_entity


def test_short_field_validator_nulls_abnormally_long_value() -> None:
    entity = {field: None for field in DEFENDANT_FIELDS}
    entity.update(full_name="Người Synthetic A", occupation="x" * 81, warnings=[])

    validate_defendant_entity(entity)

    assert entity["occupation"] is None
    assert "field_too_long:occupation" in entity["warnings"]
    assert entity["needs_review"] is True


def test_defendant_name_validator_rejects_decision_anchor() -> None:
    entity = {field: None for field in DEFENDANT_FIELDS}
    entity.update(full_name="Quyết định đưa vụ án ra xét xử số 01/SYNTHETIC", warnings=[])

    validate_defendant_entity(entity)

    assert entity["full_name"] is None
    assert "defendant_name_forbidden_anchor" in entity["warnings"]


def test_document_router_recovers_judgment_without_judgment_number() -> None:
    routed = route_document(
        "\n".join(
            [
                "NHÂN DANH NƯỚC CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
                "Thành phần Hội đồng xét xử",
                "thụ lý số: 01/SYNTHETIC",
                "đối với bị cáo:",
                "NỘI DUNG VỤ ÁN",
            ]
        )
    )

    assert routed["document_type"] == "judgment_criminal_first_instance"
    assert routed["warnings"] == ["judgment_number_missing_or_ocr_lost"]


def test_correction_notice_wins_over_judgment_anchors() -> None:
    routed = route_document("Bản án số: 01/2025/HS-ST\nSửa chữa, bổ sung bản án")

    assert routed["document_type"] == "correction_notice"
