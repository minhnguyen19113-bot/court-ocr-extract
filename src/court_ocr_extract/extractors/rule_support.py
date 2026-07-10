from __future__ import annotations

from typing import Any

from court_ocr_extract.extractors.base import ExtractorBackendStatus, normalize_extraction
from court_ocr_extract.extractors.rule_parser import extract_rule_based
from court_ocr_extract.models import ExtractorOutput, FieldValue


class RuleSupportExtractor:
    name = "rule_support_only_for_validation"

    def check_available(self) -> ExtractorBackendStatus:
        return ExtractorBackendStatus(
            self.name,
            True,
            "Experimental support-only extractor. Results are marked low confidence.",
        )

    def extract_from_text(self, text: str, *, case_id: str) -> dict[str, Any]:
        output = anchor_support_output(text)
        case = {
            "case_type": _field_value(output.case_fields.get("loai_an")),
            "filing_number": _field_value(output.case_fields.get("so_thu_ly")),
            "filing_date": _field_value(output.case_fields.get("ngay_thu_ly")),
            "legal_relationship": _field_value(output.case_fields.get("quan_he_phap_luat")),
            "presiding_judge": _field_value(output.case_fields.get("chu_toa")),
        }
        participants = []
        for item in output.participants:
            participants.append(
                {
                    "procedural_role": _field_value(item.get("tu_cach_to_tung")),
                    "full_name": _field_value(item.get("ho_ten")),
                    "birth_year": _field_value(item.get("nam_sinh")),
                    "id_number": _field_value(item.get("cccd")),
                    "address": _field_value(item.get("dia_chi")),
                    "confidence": {
                        "procedural_role": 0.35,
                        "full_name": 0.35,
                        "birth_year": 0.35,
                        "id_number": 0.35,
                        "address": 0.35,
                    },
                    "evidence": {
                        "procedural_role": _field_value(item.get("tu_cach_to_tung")),
                        "full_name": _field_value(item.get("ho_ten")),
                        "birth_year": _field_value(item.get("nam_sinh")),
                        "id_number": _field_value(item.get("cccd")),
                        "address": _field_value(item.get("dia_chi")),
                    },
                    "warnings": ["Rule support extractor is not a primary extraction backend."],
                }
            )
        payload = {
            "case": case,
            "participants": participants,
            "document_warnings": [
                "rule_support_only_for_validation was selected explicitly; review all fields."
            ],
        }
        return normalize_extraction(payload)


def _field_value(field: Any) -> str | None:
    return getattr(field, "value", None) if field is not None else None


def anchor_support_output(text: str) -> ExtractorOutput:
    """Return typed rule anchors for validation and legacy merge compatibility."""
    result = extract_rule_based(text)
    case_fields = {
        "loai_an": _typed_field(result.case_info.loai_an, "heuristic_support"),
        "so_thu_ly": _typed_field(result.case_info.so_thu_ly, "heuristic_support"),
        "ngay_thu_ly": _typed_field(result.case_info.ngay_thu_ly, "heuristic_support"),
        "quan_he_phap_luat": _typed_field(
            result.case_info.quan_he_phap_luat,
            "heuristic_support",
        ),
        "chu_toa": _typed_field(result.case_info.chu_toa, "heuristic_support"),
    }
    participants = []
    for participant in result.participants:
        participants.append(
            {
                "tu_cach_to_tung": _typed_field(
                    participant.tu_cach_to_tung,
                    "heuristic_support",
                ),
                "ho_ten": _typed_field(participant.ho_ten, "heuristic_support"),
                "nam_sinh": _typed_field(participant.nam_sinh, "heuristic_support"),
                "cccd": _typed_field(participant.cccd, "heuristic_support"),
                "dia_chi": _typed_field(participant.dia_chi, "heuristic_support"),
            }
        )
    return ExtractorOutput(
        method="heuristic_support",
        case_fields=case_fields,
        participants=participants,
    )


def _typed_field(value: str | None, method: str) -> FieldValue:
    return FieldValue(
        value=value,
        confidence=0.45 if value else 0.0,
        evidence_text=value,
        reasoning_brief=(
            "Anchor regex hỗ trợ kiểm tra, không phải extractor chính."
            if value
            else None
        ),
        source_method=method,
    )
