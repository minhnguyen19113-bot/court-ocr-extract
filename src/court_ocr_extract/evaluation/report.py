from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from court_ocr_extract.evaluation.metrics import METRIC_KEYS


def build_safe_report(metrics: dict[str, Any]) -> dict[str, int | float]:
    report: dict[str, int | float] = {}
    for key in METRIC_KEYS:
        value = metrics.get(key, 0)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"Metric {key} must be numeric.")
        report[key] = value
    return report


def render_markdown(report: dict[str, int | float]) -> str:
    lines = ["# Báo cáo đánh giá", ""]
    lines.extend(f"- `{key}`: {report[key]}" for key in METRIC_KEYS)
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, int | float], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_report = build_safe_report(report)
    if output_path.suffix.lower() in {".md", ".markdown"}:
        output_path.write_text(render_markdown(safe_report), encoding="utf-8")
    else:
        output_path.write_text(
            json.dumps(safe_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return output_path
