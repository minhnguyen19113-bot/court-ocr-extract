from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from court_ocr_extract.evaluation.manifest import (
    load_gold_manifest,
    load_prediction_manifest,
)
from court_ocr_extract.evaluation.metrics import evaluate_manifests


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _records():
    gold = load_gold_manifest(FIXTURES / "gold_manifest_synthetic.jsonl")
    predictions = load_prediction_manifest(
        FIXTURES / "prediction_manifest_synthetic.jsonl"
    )
    return gold, predictions


def test_metrics_report_perfect_synthetic_match() -> None:
    gold, predictions = _records()

    metrics = evaluate_manifests(gold, predictions)

    assert metrics["page_count_match"] == 1.0
    assert metrics["section_presence_accuracy"] == 1.0
    assert metrics["field_exact_match_rate"] == 1.0
    assert metrics["participant_role_match_count"] == 1
    assert metrics["participant_field_match_rate"] == 1.0
    assert metrics["evidence_present_rate"] == 1.0
    assert metrics["source_line_ids_present_rate"] == 1.0
    assert metrics["needs_review_rate"] == 0.0
    assert metrics["warning_count"] == 0


def test_metrics_count_missing_mismatch_and_participant_extra() -> None:
    gold, predictions = _records()
    changed = deepcopy(predictions)
    changed[0]["predicted_fields"] = [
        {
            **changed[0]["predicted_fields"][1],
            "value": "different_redacted_value",
            "evidence": None,
            "source_line_ids": [],
        }
    ]
    changed[0]["predicted_participants"] = [
        {
            "role": "extra_role",
            "name_hash": "person_hash_extra",
            "fields": {},
            "source_page": None,
            "source_line_ids": [],
            "warnings": ["synthetic warning"],
        }
    ]
    changed[0]["needs_review"] = True

    metrics = evaluate_manifests(gold, changed)

    assert metrics["field_required_missing_count"] == 1
    assert metrics["field_value_mismatch_count"] == 1
    assert metrics["participant_missing_count"] == 1
    assert metrics["participant_extra_count"] == 1
    assert metrics["source_line_ids_present_rate"] < 1.0
    assert metrics["needs_review_rate"] == 1.0
    assert metrics["warning_count"] == 1
