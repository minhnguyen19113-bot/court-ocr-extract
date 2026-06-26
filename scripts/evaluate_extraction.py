from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.excel import EXCEL_HEADERS, rows_from_result
from court_ocr_extract.models import ExtractionResult


def main() -> None:
    parser = argparse.ArgumentParser(description="Đánh giá field-level từ outputs/json và annotations.")
    parser.add_argument("--pred-dir", type=Path, default=None)
    parser.add_argument("--gold", type=Path, required=True, help="JSON/JSONL/CSV annotation một dòng mỗi đương sự.")
    args = parser.parse_args()

    settings = get_settings()
    pred_dir = args.pred_dir or settings.json_dir
    gold_rows = _load_gold(args.gold)
    pred_rows = _load_predictions(pred_dir)

    metrics = _field_metrics(gold_rows, pred_rows)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


def _load_predictions(pred_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(pred_dir.glob("*.json")):
        if path.name == "batch_summary.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = ExtractionResult(**payload)
        for row in rows_from_result(result):
            item = {header: row.get(header) or "" for header in EXCEL_HEADERS}
            item["source_file"] = result.source_file or path.stem
            rows.append(item)
    return rows


def _load_gold(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as file_handle:
            return [dict(row) for row in csv.DictReader(file_handle)]
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return payload.get("rows", [])


def _field_metrics(gold_rows: list[dict[str, str]], pred_rows: list[dict[str, str]]):
    pred_by_source = defaultdict(list)
    for row in pred_rows:
        pred_by_source[row.get("source_file", "")].append(row)

    totals = {field: {"correct": 0, "total": 0, "accuracy": 0.0} for field in EXCEL_HEADERS}
    for gold in gold_rows:
        source = gold.get("source_file", "")
        index = int(gold.get("row_index", 0) or 0)
        candidates = pred_by_source.get(source, [])
        predicted = candidates[index] if index < len(candidates) else {}
        for field in EXCEL_HEADERS:
            expected_value = _norm(gold.get(field, ""))
            predicted_value = _norm(predicted.get(field, ""))
            totals[field]["total"] += 1
            if expected_value == predicted_value:
                totals[field]["correct"] += 1

    for field, item in totals.items():
        item["accuracy"] = item["correct"] / item["total"] if item["total"] else 0.0
    return totals


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


if __name__ == "__main__":
    main()
