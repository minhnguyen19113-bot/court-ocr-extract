from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from court_ocr_extract.extractors.base import PARTICIPANT_KEYS, normalize_extraction


VALID_ROLES = {
    "Bị cáo",
    "Bị hại",
    "Nguyên đơn",
    "Bị đơn",
    "Người có quyền lợi, nghĩa vụ liên quan",
    "Người liên quan",
    "Người làm chứng",
    "Đương sự",
}

STATUS_PHRASES = [
    "có mặt tại phiên tòa",
    "vắng mặt",
    "được triệu tập hợp lệ",
    "bị tạm giam",
    "bị bắt",
    "có đơn xin xét xử vắng mặt",
]


def validate_extraction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = normalize_extraction(payload)
    document_warnings = list(result.get("document_warnings", []))
    case = result["case"]

    filing_date = case.get("filing_date")
    if filing_date and not _valid_date(filing_date):
        document_warnings.append("Invalid filing_date; expected DD/MM/YYYY.")

    for participant in result["participants"]:
        _validate_participant(participant)

    if not result["participants"]:
        document_warnings.append("No participants extracted.")

    result["document_warnings"] = _dedupe(document_warnings)
    return result


def row_needs_review(payload: dict[str, Any], participant: dict[str, Any]) -> bool:
    if payload.get("document_warnings"):
        return True
    if participant.get("warnings"):
        return True
    confidence = participant.get("confidence") or {}
    important = ["procedural_role", "full_name"]
    return any(confidence.get(key, 1.0) < 0.5 for key in important)


def min_participant_confidence(payload: dict[str, Any]) -> float | None:
    values: list[float] = []
    for participant in payload.get("participants", []):
        confidence = participant.get("confidence") or {}
        for key in PARTICIPANT_KEYS:
            if confidence.get(key) is not None:
                values.append(float(confidence[key]))
    return min(values) if values else None


def _validate_participant(participant: dict[str, Any]) -> None:
    warnings = list(participant.get("warnings", []))
    role = participant.get("procedural_role")
    full_name = participant.get("full_name")
    birth_year = participant.get("birth_year")
    id_number = participant.get("id_number")

    if not role:
        warnings.append("Missing procedural_role.")
    elif role not in VALID_ROLES:
        warnings.append("Unknown procedural_role.")

    if not full_name:
        warnings.append("Missing full_name.")
    elif _looks_like_status_phrase(full_name):
        warnings.append("full_name looks like a status phrase.")

    if birth_year and not re.fullmatch(r"\d{4}", str(birth_year)):
        warnings.append("Invalid birth_year.")

    if id_number:
        digits = re.sub(r"\D", "", str(id_number))
        participant["id_number"] = digits
        if len(digits) not in {9, 12}:
            warnings.append("Invalid CCCD/CMND length.")

    confidence = participant.setdefault("confidence", {})
    evidence = participant.setdefault("evidence", {})
    for key in PARTICIPANT_KEYS:
        confidence.setdefault(key, 0.0 if participant.get(key) else 1.0)
        evidence.setdefault(key, None)
        if participant.get(key) and not evidence.get(key):
            warnings.append(f"Missing evidence for {key}.")

    participant["warnings"] = _dedupe(warnings)


def _valid_date(value: str) -> bool:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return False
    try:
        datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _looks_like_status_phrase(value: str) -> bool:
    lowered = value.casefold()
    return any(phrase.casefold() in lowered for phrase in STATUS_PHRASES)


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
