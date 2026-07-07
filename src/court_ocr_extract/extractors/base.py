from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol


CASE_KEYS = [
    "case_type",
    "filing_number",
    "filing_date",
    "legal_relationship",
    "presiding_judge",
]
PARTICIPANT_KEYS = ["procedural_role", "full_name", "birth_year", "id_number", "address"]


@dataclass(frozen=True)
class ExtractorBackendStatus:
    name: str
    available: bool
    reason: str = ""


class ExtractorBackend(Protocol):
    name: str

    def check_available(self) -> ExtractorBackendStatus:
        ...

    def extract_from_text(self, text: str, *, case_id: str) -> dict[str, Any]:
        ...


def empty_extraction() -> dict[str, Any]:
    return {
        "case": {key: None for key in CASE_KEYS},
        "participants": [],
        "document_warnings": [],
    }


def normalize_extraction(payload: dict[str, Any]) -> dict[str, Any]:
    case = payload.get("case") or {}
    participants = payload.get("participants") or []
    normalized = empty_extraction()
    normalized["case"] = {key: _none_if_empty(case.get(key)) for key in CASE_KEYS}
    normalized["participants"] = [_normalize_participant(item) for item in participants if isinstance(item, dict)]
    normalized["document_warnings"] = [str(item) for item in payload.get("document_warnings", []) if item]
    return normalized


def parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("Extractor did not return a JSON object.")
    return payload


def _normalize_participant(item: dict[str, Any]) -> dict[str, Any]:
    participant = {key: _none_if_empty(item.get(key)) for key in PARTICIPANT_KEYS}
    confidence = item.get("confidence") if isinstance(item.get("confidence"), dict) else {}
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    participant["confidence"] = {
        key: float(confidence.get(key) or 0.0) for key in PARTICIPANT_KEYS
    }
    participant["evidence"] = {key: _none_if_empty(evidence.get(key)) for key in PARTICIPANT_KEYS}
    participant["warnings"] = [str(value) for value in item.get("warnings", []) if value]
    return participant


def _none_if_empty(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value
