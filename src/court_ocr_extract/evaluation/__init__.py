"""Privacy-aware evaluation contracts for redacted gold and prediction manifests."""

from court_ocr_extract.evaluation.manifest import (
    ManifestValidationError,
    load_gold_manifest,
    load_prediction_manifest,
)
from court_ocr_extract.evaluation.metrics import evaluate_manifests
from court_ocr_extract.evaluation.report import build_safe_report, write_report

__all__ = [
    "ManifestValidationError",
    "build_safe_report",
    "evaluate_manifests",
    "load_gold_manifest",
    "load_prediction_manifest",
    "write_report",
]
