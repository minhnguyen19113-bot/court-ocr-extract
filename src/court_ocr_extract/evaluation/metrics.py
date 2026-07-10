from __future__ import annotations

import json
import re
from typing import Any


METRIC_KEYS = [
    "cases_total",
    "page_count_match",
    "empty_page_rate",
    "bbox_coverage_rate",
    "low_confidence_line_rate",
    "section_presence_accuracy",
    "field_exact_match_rate",
    "field_required_missing_count",
    "field_unexpected_count",
    "field_value_mismatch_count",
    "field_evidence_coverage_rate",
    "participant_role_match_count",
    "participant_missing_count",
    "participant_extra_count",
    "participant_field_match_rate",
    "evidence_present_rate",
    "source_page_present_rate",
    "source_line_ids_present_rate",
    "needs_review_rate",
    "warning_count",
]


def evaluate_manifests(
    gold_records: list[dict[str, Any]],
    prediction_records: list[dict[str, Any]],
) -> dict[str, int | float]:
    predictions = {item["case_id_hash"]: item for item in prediction_records}
    gold_ids = {item["case_id_hash"] for item in gold_records}

    page_matches = 0
    empty_pages = processed_pages = bbox_lines = low_confidence_lines = ocr_lines = 0
    section_correct = section_total = 0
    field_exact = field_total = required_missing = unexpected_fields = mismatches = 0
    evidence_present = 0
    participant_role_matches = participant_missing = participant_extra = 0
    participant_field_matches = participant_field_total = 0
    source_page_present = source_line_ids_present = source_item_total = 0
    needs_review_count = 0

    for gold in gold_records:
        prediction = predictions.get(gold["case_id_hash"])
        if prediction is None:
            prediction = _empty_prediction(gold["case_id_hash"])
            needs_review_count += 1
        elif prediction.get("needs_review"):
            needs_review_count += 1

        if int(gold.get("page_count", 0)) == int(prediction.get("page_count_processed", 0)):
            page_matches += 1
        ocr = prediction.get("ocr_metrics") or {}
        processed_pages += int(prediction.get("page_count_processed", 0) or 0)
        empty_pages += int(ocr.get("empty_page_count", 0) or 0)
        ocr_lines += int(ocr.get("line_count", 0) or 0)
        bbox_lines += int(ocr.get("bbox_line_count", 0) or 0)
        low_confidence_lines += int(ocr.get("low_confidence_line_count", 0) or 0)

        predicted_sections = {
            item.get("section_name"): item
            for item in prediction.get("predicted_sections", [])
        }
        for expected in gold.get("expected_sections", []):
            section_total += 1
            predicted = predicted_sections.get(expected.get("section_name"), {})
            if bool(expected.get("expected_present")) == bool(predicted.get("present")):
                section_correct += 1

        expected_fields = {
            item.get("field_name"): item for item in gold.get("expected_fields", [])
        }
        predicted_fields = {
            item.get("field_name"): item
            for item in prediction.get("predicted_fields", [])
        }
        unexpected_fields += len(set(predicted_fields) - set(expected_fields))
        for field_name, expected in expected_fields.items():
            field_total += 1
            predicted = predicted_fields.get(field_name)
            if predicted is None or predicted.get("value") in (None, ""):
                if expected.get("required"):
                    required_missing += 1
            elif _normalized(predicted.get("value")) == _normalized(expected.get("expected_value")):
                field_exact += 1
            else:
                mismatches += 1
            if predicted and predicted.get("evidence"):
                evidence_present += 1
            source_item_total += 1
            if predicted and predicted.get("source_page") is not None:
                source_page_present += 1
            if predicted and predicted.get("source_line_ids"):
                source_line_ids_present += 1

        participant_metrics = _participant_metrics(
            gold.get("expected_participants", []),
            prediction.get("predicted_participants", []),
        )
        participant_role_matches += participant_metrics["role_matches"]
        participant_missing += participant_metrics["missing"]
        participant_extra += participant_metrics["extra"]
        participant_field_matches += participant_metrics["field_matches"]
        participant_field_total += participant_metrics["field_total"]
        source_page_present += participant_metrics["source_page_present"]
        source_line_ids_present += participant_metrics["source_line_ids_present"]
        source_item_total += participant_metrics["source_item_total"]

    for prediction in prediction_records:
        if prediction["case_id_hash"] not in gold_ids:
            unexpected_fields += len(prediction.get("predicted_fields", []))
            participant_extra += len(prediction.get("predicted_participants", []))

    warning_count = sum(_warning_count(item) for item in prediction_records)
    cases_total = len(gold_records)
    metrics: dict[str, int | float] = {
        "cases_total": cases_total,
        "page_count_match": _rate(page_matches, cases_total),
        "empty_page_rate": _rate(empty_pages, processed_pages),
        "bbox_coverage_rate": _rate(bbox_lines, ocr_lines),
        "low_confidence_line_rate": _rate(low_confidence_lines, ocr_lines),
        "section_presence_accuracy": _rate(section_correct, section_total),
        "field_exact_match_rate": _rate(field_exact, field_total),
        "field_required_missing_count": required_missing,
        "field_unexpected_count": unexpected_fields,
        "field_value_mismatch_count": mismatches,
        "field_evidence_coverage_rate": _rate(evidence_present, field_total),
        "participant_role_match_count": participant_role_matches,
        "participant_missing_count": participant_missing,
        "participant_extra_count": participant_extra,
        "participant_field_match_rate": _rate(
            participant_field_matches,
            participant_field_total,
        ),
        "evidence_present_rate": _rate(evidence_present, field_total),
        "source_page_present_rate": _rate(source_page_present, source_item_total),
        "source_line_ids_present_rate": _rate(
            source_line_ids_present,
            source_item_total,
        ),
        "needs_review_rate": _rate(needs_review_count, cases_total),
        "warning_count": warning_count,
    }
    return {key: metrics[key] for key in METRIC_KEYS}


def _participant_metrics(
    expected: list[dict[str, Any]],
    predicted: list[dict[str, Any]],
) -> dict[str, int]:
    remaining = list(predicted)
    result = {
        "role_matches": 0,
        "missing": 0,
        "extra": 0,
        "field_matches": 0,
        "field_total": 0,
        "source_page_present": 0,
        "source_line_ids_present": 0,
        "source_item_total": 0,
    }
    for expected_item in expected:
        match_index = _participant_match_index(expected_item, remaining)
        result["source_item_total"] += 1
        if match_index is None:
            result["missing"] += 1
            result["field_total"] += len(expected_item.get("fields") or {})
            continue
        predicted_item = remaining.pop(match_index)
        if _normalized(expected_item.get("role")) == _normalized(predicted_item.get("role")):
            result["role_matches"] += 1
        if predicted_item.get("source_page") is not None:
            result["source_page_present"] += 1
        if predicted_item.get("source_line_ids"):
            result["source_line_ids_present"] += 1
        predicted_fields = predicted_item.get("fields") or {}
        for key, expected_value in (expected_item.get("fields") or {}).items():
            result["field_total"] += 1
            if _normalized(expected_value) == _normalized(predicted_fields.get(key)):
                result["field_matches"] += 1
    result["extra"] = len(remaining)
    return result


def _participant_match_index(
    expected: dict[str, Any],
    predicted: list[dict[str, Any]],
) -> int | None:
    name_hash = expected.get("name_hash")
    if name_hash:
        for index, item in enumerate(predicted):
            if item.get("name_hash") == name_hash:
                return index
    role = _normalized(expected.get("role"))
    for index, item in enumerate(predicted):
        if _normalized(item.get("role")) == role:
            return index
    return None


def _warning_count(prediction: dict[str, Any]) -> int:
    total = len(prediction.get("warnings") or [])
    total += sum(len(item.get("warnings") or []) for item in prediction.get("predicted_fields", []))
    total += sum(len(item.get("warnings") or []) for item in prediction.get("predicted_participants", []))
    return total


def _empty_prediction(case_id_hash: str) -> dict[str, Any]:
    return {
        "case_id_hash": case_id_hash,
        "page_count_processed": 0,
        "ocr_metrics": {},
        "predicted_sections": [],
        "predicted_fields": [],
        "predicted_participants": [],
        "warnings": [],
        "needs_review": True,
    }


def _normalized(value: Any) -> str:
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value.strip().casefold())
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0
