from __future__ import annotations

import json
from pathlib import Path

import pytest

from court_ocr_extract.evaluation.manifest import (
    ManifestValidationError,
    load_gold_manifest,
    load_prediction_manifest,
)
from court_ocr_extract.evaluation.privacy import (
    hash_value,
    looks_like_pii,
    redact_common_pii,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_synthetic_gold_and_prediction_manifests_are_valid() -> None:
    gold = load_gold_manifest(FIXTURES / "gold_manifest_synthetic.jsonl")
    predictions = load_prediction_manifest(
        FIXTURES / "prediction_manifest_synthetic.jsonl"
    )

    assert gold[0]["case_id_hash"] == predictions[0]["case_id_hash"]
    assert gold[0]["review"]["review_status"] == "approved"


def test_privacy_helper_detects_and_redacts_common_pii() -> None:
    raw = "contact@example.com 0901234567 123456789012"

    assert looks_like_pii(raw)
    assert not looks_like_pii("synthetic redacted text")
    assert redact_common_pii(raw) == (
        "<redacted_email> <redacted_phone> <redacted_id>"
    )
    assert hash_value("synthetic", salt="test").startswith("sha256:")


def test_gold_manifest_rejects_obvious_pii_without_echoing_value(tmp_path: Path) -> None:
    record = load_gold_manifest(FIXTURES / "gold_manifest_synthetic.jsonl")[0]
    record["review"]["notes"] = "contact@example.com"
    path = tmp_path / "gold.jsonl"
    path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(ManifestValidationError) as error:
        load_gold_manifest(path)

    assert "obvious PII pattern" in str(error.value)
    assert "contact@example.com" not in str(error.value)


def test_hash_field_does_not_hide_raw_identity_number(tmp_path: Path) -> None:
    record = load_gold_manifest(FIXTURES / "gold_manifest_synthetic.jsonl")[0]
    record["expected_participants"][0]["name_hash"] = "123456789012"
    path = tmp_path / "gold.jsonl"
    path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(ManifestValidationError) as error:
        load_gold_manifest(path)

    assert "expected_participants[0].name_hash" in str(error.value)
    assert "123456789012" not in str(error.value)
