from __future__ import annotations

from typing import Any


CASE_FIELD_KEYS = [
    "loai_an",
    "so_thu_ly",
    "ngay_thu_ly",
    "quan_he_phap_luat",
    "chu_toa",
]

PARTICIPANT_FIELD_KEYS = [
    "tu_cach_to_tung",
    "ho_ten",
    "nam_sinh",
    "cccd",
    "dia_chi",
]

FIELD_VALUE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["value", "confidence", "evidence_text", "reasoning_brief"],
    "properties": {
        "value": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_text": {"type": ["string", "null"]},
        "reasoning_brief": {"type": ["string", "null"]},
    },
}

EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["case_info", "participants", "warnings"],
    "properties": {
        "case_info": {
            "type": "object",
            "additionalProperties": False,
            "required": CASE_FIELD_KEYS,
            "properties": {key: FIELD_VALUE_SCHEMA for key in CASE_FIELD_KEYS},
        },
        "participants": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": PARTICIPANT_FIELD_KEYS,
                "properties": {key: FIELD_VALUE_SCHEMA for key in PARTICIPANT_FIELD_KEYS},
            },
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
}


def empty_field(source_method: str, reason: str = "Không thấy dữ liệu trong OCR text.") -> dict[str, Any]:
    return {
        "value": None,
        "confidence": 0.0,
        "evidence_text": None,
        "reasoning_brief": reason,
        "source_method": source_method,
    }
