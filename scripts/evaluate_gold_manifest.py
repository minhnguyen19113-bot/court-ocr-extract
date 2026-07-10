from __future__ import annotations

import argparse
import json

from court_ocr_extract.evaluation.manifest import (
    ManifestValidationError,
    load_gold_manifest,
    load_prediction_manifest,
)
from court_ocr_extract.evaluation.metrics import evaluate_manifests
from court_ocr_extract.evaluation.report import build_safe_report, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate redacted JSONL manifests and print aggregate metrics only."
    )
    parser.add_argument("--gold", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        gold = load_gold_manifest(args.gold)
        predictions = load_prediction_manifest(args.predictions)
    except ManifestValidationError as exc:
        print(f"Evaluation manifest: FAIL ({exc})")
        return 1

    report = build_safe_report(evaluate_manifests(gold, predictions))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.output:
        write_report(report, args.output)
        print("Report written: yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
