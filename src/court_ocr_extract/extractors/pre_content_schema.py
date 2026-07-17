from __future__ import annotations

from copy import deepcopy
from typing import Any


METADATA_FIELDS = (
    "court_name",
    "judgment_number",
    "judgment_date",
    "case_type",
    "legal_relationship",
    "trial_location_or_date_sentence",
    "case_acceptance_number",
    "case_acceptance_date",
    "trial_decision_number",
    "postponement_decision_number",
)
TRIAL_PANEL_FIELDS = ("presiding_judge", "jurors", "clerk", "prosecutor")
DEFENDANT_FIELDS = (
    "full_name", "alias", "birth_date_or_year", "birth_place", "gender",
    "nationality", "ethnicity", "religion", "education", "occupation",
    "permanent_address", "current_address", "father_name", "mother_name",
    "spouse", "children", "criminal_record", "detention_status", "presence_status", "cccd",
)
PARTICIPANT_FIELDS = (
    "role", "full_name", "birth_date_or_year", "cccd", "address", "presence_status",
    "represented_person", "relationship",
)


def empty_pre_content_output(document_type: str = "unknown") -> dict[str, Any]:
    return {
        "document_type": document_type,
        "metadata": {field: None for field in METADATA_FIELDS},
        "trial_panel": {
            "presiding_judge": None,
            "jurors": [],
            "clerk": None,
            "prosecutor": None,
        },
        "defendants": [],
        "participants": [],
        "evidence": [],
        "warnings": [],
        "needs_review": document_type == "unknown",
        "field_meta": {},
    }


def normalize_pre_content_output(payload: Any, *, document_type: str = "unknown") -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    output = empty_pre_content_output(str(source.get("document_type") or document_type))
    for group, fields in (("metadata", METADATA_FIELDS), ("trial_panel", TRIAL_PANEL_FIELDS)):
        values = source.get(group) if isinstance(source.get(group), dict) else {}
        for field in fields:
            value = values.get(field)
            if field == "jurors":
                output[group][field] = [str(item).strip() for item in value or [] if str(item).strip()]
            else:
                output[group][field] = _clean(value)
    output["defendants"] = [
        _normalize_entity(item, DEFENDANT_FIELDS) for item in source.get("defendants", [])
        if isinstance(item, dict)
    ]
    output["participants"] = [
        _normalize_entity(item, PARTICIPANT_FIELDS) for item in source.get("participants", [])
        if isinstance(item, dict)
    ]
    output["evidence"] = [deepcopy(item) for item in source.get("evidence", []) if isinstance(item, dict)]
    output["warnings"] = [str(item) for item in source.get("warnings", []) if item]
    output["needs_review"] = bool(source.get("needs_review", False) or output["document_type"] == "unknown")
    output["field_meta"] = deepcopy(source.get("field_meta", {})) if isinstance(source.get("field_meta"), dict) else {}
    return output


def unresolved_field_paths(output: dict[str, Any]) -> list[str]:
    paths = []
    for group in ("metadata", "trial_panel"):
        for field, value in output[group].items():
            if value in (None, "", []):
                paths.append(f"{group}.{field}")
    if not output["defendants"]:
        paths.append("defendants")
    if not output["participants"]:
        paths.append("participants")
    return paths


def flatten_output(output: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for group in ("metadata", "trial_panel"):
        for field, value in output.get(group, {}).items():
            flat[f"{group}.{field}"] = value
    flat["defendants"] = output.get("defendants", [])
    flat["participants"] = output.get("participants", [])
    return flat


def _normalize_entity(item: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    normalized = {field: _clean(item.get(field)) for field in fields}
    normalized.update(
        {
            "raw_block": str(item.get("raw_block") or "").strip(),
            "evidence_line_ids": [str(value) for value in item.get("evidence_line_ids", []) if value],
            "source_block_id": str(item.get("source_block_id") or "").strip(),
            "entity_id": str(item.get("entity_id") or item.get("source_block_id") or "").strip(),
            "source_region": str(item.get("source_region") or "").strip(),
            "needs_review": bool(item.get("needs_review", False)),
            "warnings": [str(value) for value in item.get("warnings", []) if value],
        }
    )
    return normalized


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value
