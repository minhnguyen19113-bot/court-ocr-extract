from __future__ import annotations

from typing import Any

from court_ocr_extract.extraction.rule_support import anchor_support_output
from court_ocr_extract.extractors.base import ExtractorBackendStatus, normalize_extraction


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
