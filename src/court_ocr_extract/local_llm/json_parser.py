from __future__ import annotations

import json
import re
from typing import Any


class StrictJsonError(ValueError):
    pass


CASE_KEY_MAP = {
    "case_type": "loai_an",
    "docket_number": "so_thu_ly",
    "docket_date": "ngay_thu_ly",
    "legal_relationship": "quan_he_phap_luat",
    "presiding_judge": "chu_toa",
}

PARTY_KEY_MAP = {
    "litigation_role": "tu_cach_to_tung",
    "full_name": "ho_ten",
    "birth_year": "nam_sinh",
    "citizen_id": "cccd",
    "address": "dia_chi",
}


def parse_json_object(content: str) -> dict[str, Any]:
    content = _strip_markdown_fence(content.strip())
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise StrictJsonError(f"Invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise StrictJsonError("Local LLM output must be a JSON object.")
    return payload


def normalize_extraction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept the requested public schema or the legacy internal schema."""
    if "case_info" in payload:
        return _normalize_internal_payload(payload)
    return _normalize_public_payload(payload)


def _normalize_internal_payload(payload: dict[str, Any]) -> dict[str, Any]:
    case_info = payload.get("case_info") or {}
    normalized_case = {}
    for key in CASE_KEY_MAP.values():
        normalized_case[key] = _field_object(case_info.get(key), _confidence(payload, key))

    participants = []
    for participant in payload.get("participants") or []:
        participants.append(
            {
                key: _field_object(participant.get(key), _confidence(payload, key))
                for key in PARTY_KEY_MAP.values()
            }
        )
    return {
        "case_info": normalized_case,
        "participants": participants,
        "warnings": _string_list(payload.get("warnings")),
        "reasoning_summary": payload.get("reasoning_summary"),
    }


def _normalize_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_case = {}
    for public_key, internal_key in CASE_KEY_MAP.items():
        normalized_case[internal_key] = _field_object(
            payload.get(public_key),
            _confidence(payload, public_key, internal_key),
            reasoning=payload.get("reasoning_summary") if public_key == "legal_relationship" else None,
            evidence=_evidence(payload, public_key, internal_key),
        )

    participants = []
    for party in payload.get("parties") or []:
        if not isinstance(party, dict):
            continue
        participants.append(
            {
                internal_key: _field_object(
                    party.get(public_key),
                    _confidence(payload, public_key, internal_key),
                    evidence=_evidence(party, public_key, internal_key),
                )
                for public_key, internal_key in PARTY_KEY_MAP.items()
            }
        )

    return {
        "case_info": normalized_case,
        "participants": participants,
        "warnings": _string_list(payload.get("warnings")),
        "reasoning_summary": payload.get("reasoning_summary"),
    }


def _field_object(
    value: Any,
    confidence: float | None,
    reasoning: str | None = None,
    evidence: Any = None,
) -> dict[str, Any]:
    if isinstance(value, dict):
        raw_value = value.get("value")
        confidence = _safe_confidence(value.get("confidence"), confidence)
        return {
            "value": _clean_scalar(raw_value),
            "confidence": confidence,
            "evidence_text": _clean_scalar(value.get("evidence_text") or evidence),
            "reasoning_brief": _clean_scalar(value.get("reasoning_brief") or reasoning),
        }
    clean_value = _clean_scalar(value)
    return {
        "value": clean_value,
        "confidence": confidence if clean_value else 0.0,
        "evidence_text": _clean_scalar(evidence),
        "reasoning_brief": reasoning,
    }


def _confidence(payload: dict[str, Any], *keys: str) -> float:
    values = payload.get("confidence_by_field") or {}
    if not isinstance(values, dict):
        return 0.0
    for key in keys:
        if key in values:
            return _safe_confidence(values.get(key), 0.0)
    return 0.0


def _evidence(payload: dict[str, Any], *keys: str) -> str | None:
    values = payload.get("evidence_by_field") or {}
    if not isinstance(values, dict):
        return None
    for key in keys:
        if key in values:
            return _clean_scalar(values.get(key))
    return None


def _safe_confidence(value: Any, default: float | None = 0.0) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return float(default or 0.0)
    return max(0.0, min(1.0, confidence))


def _clean_scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _strip_markdown_fence(content: str) -> str:
    if not content.startswith("```"):
        return content
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    return content.strip()
