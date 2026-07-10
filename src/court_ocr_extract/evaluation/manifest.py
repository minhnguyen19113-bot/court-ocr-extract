from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from court_ocr_extract.evaluation.privacy import find_pii_paths


GOLD_REQUIRED = {
    "case_id_hash",
    "file_hash",
    "source_type",
    "split",
    "page_count",
    "document_tags",
    "expected_sections",
    "expected_fields",
    "expected_participants",
    "review",
}

PREDICTION_REQUIRED = {
    "case_id_hash",
    "run_id",
    "ocr_backend",
    "ocr_backend_version",
    "extractor_backend",
    "model_name",
    "prompt_version",
    "page_count_processed",
    "ocr_metrics",
    "predicted_sections",
    "predicted_fields",
    "predicted_participants",
    "warnings",
    "needs_review",
}


class ManifestValidationError(ValueError):
    pass


def load_gold_manifest(path: str | Path) -> list[dict[str, Any]]:
    return _load_jsonl(path, validate_gold_record, "gold")


def load_prediction_manifest(path: str | Path) -> list[dict[str, Any]]:
    return _load_jsonl(path, validate_prediction_record, "prediction")


def validate_gold_record(record: dict[str, Any]) -> list[str]:
    errors = _missing_keys(record, GOLD_REQUIRED)
    errors.extend(_type_errors(record, "page_count", int, minimum=0))
    errors.extend(_list_errors(record, ["document_tags", "expected_sections", "expected_fields", "expected_participants"]))
    if not isinstance(record.get("review"), dict):
        errors.append("review must be an object")
    else:
        errors.extend(_missing_keys(record["review"], {"reviewer", "review_status", "notes"}, "review"))

    for index, item in enumerate(record.get("expected_sections") or []):
        errors.extend(
            _object_with_keys(
                item,
                {"section_name", "expected_present", "source_page"},
                f"expected_sections[{index}]",
            )
        )
    for index, item in enumerate(record.get("expected_fields") or []):
        errors.extend(
            _object_with_keys(
                item,
                {
                    "field_name",
                    "expected_value",
                    "value_type",
                    "source_page",
                    "source_line_ids",
                    "evidence_text_redacted",
                    "required",
                },
                f"expected_fields[{index}]",
            )
        )
    for index, item in enumerate(record.get("expected_participants") or []):
        errors.extend(
            _object_with_keys(
                item,
                {"role", "name_hash", "fields", "source_page", "source_line_ids"},
                f"expected_participants[{index}]",
            )
        )

    pii_paths = find_pii_paths(record)
    if pii_paths:
        errors.append("obvious PII pattern detected at " + ", ".join(pii_paths))
    return errors


def validate_prediction_record(record: dict[str, Any]) -> list[str]:
    errors = _missing_keys(record, PREDICTION_REQUIRED)
    errors.extend(_type_errors(record, "page_count_processed", int, minimum=0))
    errors.extend(_list_errors(record, ["predicted_sections", "predicted_fields", "predicted_participants", "warnings"]))
    if not isinstance(record.get("ocr_metrics"), dict):
        errors.append("ocr_metrics must be an object")
    for index, item in enumerate(record.get("predicted_sections") or []):
        errors.extend(
            _object_with_keys(
                item,
                {"section_name", "present", "source_page"},
                f"predicted_sections[{index}]",
            )
        )
    for index, item in enumerate(record.get("predicted_fields") or []):
        errors.extend(
            _object_with_keys(
                item,
                {"field_name", "value", "source_page", "source_line_ids", "evidence", "confidence", "warnings"},
                f"predicted_fields[{index}]",
            )
        )
    for index, item in enumerate(record.get("predicted_participants") or []):
        errors.extend(
            _object_with_keys(
                item,
                {"role", "name_hash", "fields", "source_page", "source_line_ids", "warnings"},
                f"predicted_participants[{index}]",
            )
        )
    pii_paths = find_pii_paths(record)
    if pii_paths:
        errors.append("obvious PII pattern detected at " + ", ".join(pii_paths))
    return errors


def _load_jsonl(
    path: str | Path,
    validator: Callable[[dict[str, Any]], list[str]],
    kind: str,
) -> list[dict[str, Any]]:
    path = Path(path)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_case_ids: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ManifestValidationError(f"Cannot read {kind} manifest.") from exc

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line {line_number}: invalid JSON")
            continue
        if not isinstance(record, dict):
            errors.append(f"line {line_number}: record must be an object")
            continue
        record_errors = validator(record)
        errors.extend(f"line {line_number}: {error}" for error in record_errors)
        case_id = record.get("case_id_hash")
        if isinstance(case_id, str):
            if case_id in seen_case_ids:
                errors.append(f"line {line_number}: duplicate case_id_hash")
            seen_case_ids.add(case_id)
        records.append(record)

    if not records and not errors:
        errors.append("manifest is empty")
    if errors:
        raise ManifestValidationError("; ".join(errors))
    return records


def _missing_keys(
    value: dict[str, Any],
    required: set[str],
    label: str = "record",
) -> list[str]:
    missing = sorted(required - value.keys())
    return [f"{label} missing required field: {key}" for key in missing]


def _object_with_keys(value: Any, required: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    return _missing_keys(value, required, label)


def _list_errors(value: dict[str, Any], keys: list[str]) -> list[str]:
    return [f"{key} must be an array" for key in keys if not isinstance(value.get(key), list)]


def _type_errors(
    value: dict[str, Any],
    key: str,
    expected_type: type,
    *,
    minimum: int | None = None,
) -> list[str]:
    item = value.get(key)
    if not isinstance(item, expected_type) or isinstance(item, bool):
        return [f"{key} must be {expected_type.__name__}"]
    if minimum is not None and item < minimum:
        return [f"{key} must be >= {minimum}"]
    return []
