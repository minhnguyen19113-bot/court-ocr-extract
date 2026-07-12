from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from court_ocr_extract.extractors.hybrid_pre_content_extractor import HybridPreContentExtractor
from court_ocr_extract.extractors.llm_only_pre_content_extractor import LLMCallable, LLMOnlyPreContentExtractor
from court_ocr_extract.extractors.pre_content_schema import flatten_output
from court_ocr_extract.extractors.pre_content_segmenter import segment_pre_content
from court_ocr_extract.extractors.rule_based_pre_content_extractor import extract_pre_content_rules
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.settings import PipelineSettings
from court_ocr_extract.visual_debug import escape, write_html


STRATEGIES = ("hybrid_rule_llm", "llm_only")


def run_pre_content_ab_test(
    records: list[OCRCacheRecord],
    *,
    output_dir: str | Path,
    settings: PipelineSettings,
    strategies: list[str] | None = None,
    limit: int | None = None,
    llm_callable: LLMCallable | None = None,
) -> dict[str, Any]:
    selected = records[:limit] if limit is not None else records
    requested = strategies or list(STRATEGIES)
    unknown = [name for name in requested if name not in STRATEGIES]
    if unknown:
        raise ValueError(f"Unsupported pre-content strategies: {', '.join(unknown)}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    hybrid = HybridPreContentExtractor(settings, llm_callable=llm_callable)
    llm_only = LLMOnlyPreContentExtractor(settings, llm_callable=llm_callable)
    cases = []
    for record in selected:
        case_dir = output_dir / "cases" / record.case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        segment = segment_pre_content(record.result)
        rule = extract_pre_content_rules(segment)
        correction = segment["document_type"] == "correction_notice"
        hybrid_output = _skipped_output(segment, "correction_notice_not_in_judgment_benchmark") if correction else None
        llm_output = _skipped_output(segment, "correction_notice_not_in_judgment_benchmark") if correction else None
        if not correction and "hybrid_rule_llm" in requested:
            hybrid_output = hybrid.extract(segment, case_id=record.case_id)
        if not correction and "llm_only" in requested:
            llm_output = llm_only.extract(segment, case_id=record.case_id)
        hybrid_output = hybrid_output or _skipped_output(segment, "strategy_not_requested")
        llm_output = llm_output or _skipped_output(segment, "strategy_not_requested")
        compare = compare_outputs(hybrid_output, llm_output)
        metrics = _case_metrics(segment, hybrid_output, llm_output, compare)
        case = {
            "case_id": record.case_id,
            "segmenter": segment,
            "rule_output": rule,
            "hybrid_output": hybrid_output,
            "llm_only_output": llm_output,
            "compare": compare,
            "metrics": metrics,
            "benchmark_included": not correction and segment["document_type"] == "judgment_criminal_first_instance",
        }
        _write_case(case_dir, case)
        cases.append(case)
    summary = _summary(cases, requested)
    _write_json(output_dir / "compare_summary.json", summary)
    _write_workbook(output_dir / "compare_summary.xlsx", cases, summary)
    _write_index(output_dir / "index.html", cases)
    return summary


def compare_outputs(hybrid: dict[str, Any], llm_only: dict[str, Any]) -> dict[str, Any]:
    left, right = flatten_output(hybrid), flatten_output(llm_only)
    rows = []
    for field in sorted(set(left) | set(right)):
        left_value, right_value = left.get(field), right.get(field)
        if left_value in (None, "", []) and right_value in (None, "", []):
            status = "missing_both"
        elif left_value == right_value:
            status = "same"
        elif left_value in (None, "", []) or right_value in (None, "", []):
            status = "missing_one"
        else:
            status = "different"
        rows.append({"field": field, "hybrid": left_value, "llm_only": right_value, "status": status})
    return {
        "fields": rows,
        "disagreement_count": sum(row["status"] in {"different", "missing_one"} for row in rows),
        "conflict_count": len(hybrid.get("conflicts", [])),
    }


def _case_metrics(segment, hybrid, llm_only, compare) -> dict[str, Any]:
    hybrid_flat = flatten_output(hybrid)
    values = list(hybrid_flat.values())
    evidence_fields = {item.get("field") for item in hybrid.get("evidence", []) if item.get("field")}
    present_fields = [field for field, value in hybrid_flat.items() if value not in (None, "", [])]
    return {
        "field_present_count": len(present_fields),
        "field_missing_count": sum(value in (None, "", []) for value in values),
        "conflict_count": len(hybrid.get("conflicts", [])),
        "needs_review_count": int(bool(hybrid.get("needs_review"))) + int(bool(llm_only.get("needs_review"))),
        "evidence_coverage_rate": round(len(evidence_fields & set(present_fields)) / max(1, len(present_fields)), 4),
        "participant_count": len(hybrid.get("participants", [])),
        "defendant_count": len(hybrid.get("defendants", [])),
        "document_type_detected": segment.get("document_type"),
        "segment_stop_found": bool(segment.get("stop_line_id")),
        "llm_json_valid": bool(llm_only.get("llm_json_valid", False)),
        "hybrid_vs_llm_disagreement_count": compare["disagreement_count"],
    }


def _summary(cases: list[dict[str, Any]], strategies: list[str]) -> dict[str, Any]:
    return {
        "task": "pre_content_extraction_ab_test",
        "strategies": strategies,
        "case_count": len(cases),
        "judgment_benchmark_count": sum(case["benchmark_included"] for case in cases),
        "correction_notice_count": sum(case["segmenter"]["document_type"] == "correction_notice" for case in cases),
        "unknown_document_count": sum(case["segmenter"]["document_type"] == "unknown" for case in cases),
        "totals": {
            key: sum(case["metrics"].get(key, 0) for case in cases)
            for key in (
                "field_present_count", "field_missing_count", "conflict_count", "needs_review_count",
                "participant_count", "defendant_count", "hybrid_vs_llm_disagreement_count",
            )
        },
        "cases": [
            {"case_id": case["case_id"], "benchmark_included": case["benchmark_included"], **case["metrics"]}
            for case in cases
        ],
    }


def _write_case(case_dir: Path, case: dict[str, Any]) -> None:
    (case_dir / "pre_content_text.md").write_text(case["segmenter"]["pre_content_text"], encoding="utf-8")
    for key, filename in (
        ("segmenter", "segmenter.json"), ("rule_output", "rule_output.json"),
        ("hybrid_output", "hybrid_output.json"), ("llm_only_output", "llm_only_output.json"),
        ("compare", "compare.json"),
    ):
        _write_json(case_dir / filename, case[key])
    _write_case_review(case_dir / "review.html", case)


def _write_case_review(path: Path, case: dict[str, Any]) -> None:
    rows = []
    for item in case["compare"]["fields"]:
        css = "same" if item["status"] == "same" else "attention"
        rows.append(
            f'<tr class="{css}"><td>{escape(item["field"])}</td><td>{escape(_display(item["hybrid"]))}</td>'
            f'<td>{escape(_display(item["llm_only"]))}</td><td>{escape(item["status"])}</td></tr>'
        )
    source_lines = "".join(
        f'<div id="{escape(line.get("line_id"))}"><code>{escape(line.get("line_id"))}</code> '
        f'{escape(line.get("text"))}</div>'
        for line in case["segmenter"].get("pre_content_lines", [])
    )
    body = (
        f'<h1>{escape(case["case_id"])}</h1><p>Document type: {escape(case["segmenter"]["document_type"])}</p>'
        '<div class="grid"><section><h2>Pre-content text</h2>'
        f'<div>{source_lines}</div></section>'
        f'<section><h2>Hybrid</h2><pre>{escape(_display(case["hybrid_output"]))}</pre></section>'
        f'<section><h2>LLM-only</h2><pre>{escape(_display(case["llm_only_output"]))}</pre></section></div>'
        '<h2>Field compare</h2><table><tr><th>Field</th><th>Hybrid</th><th>LLM-only</th><th>Status</th></tr>'
        + "".join(rows) + "</table><h2>Evidence</h2>"
        + _evidence_table(case["hybrid_output"], "hybrid")
        + _evidence_table(case["llm_only_output"], "llm_only")
    )
    write_html(path, "Pre-content A/B review", body)


def _write_index(path: Path, cases: list[dict[str, Any]]) -> None:
    rows = []
    for case in cases:
        metrics = case["metrics"]
        rows.append(
            f'<tr><td><a href="cases/{escape(case["case_id"])}/review.html">{escape(case["case_id"])}</a></td>'
            f'<td>{escape(metrics["document_type_detected"])}</td><td>{escape(case["benchmark_included"])}</td>'
            f'<td>{escape(metrics["field_present_count"])}</td><td>{escape(metrics["field_missing_count"])}</td>'
            f'<td>{escape(metrics["hybrid_vs_llm_disagreement_count"])}</td><td>{escape(metrics["needs_review_count"])}</td></tr>'
        )
    body = (
        '<h1>Pre-content extraction A/B test</h1><p>Hybrid rule+LLM so với LLM-only; correction notice không tính vào benchmark bản án.</p>'
        '<table><tr><th>Case</th><th>Document type</th><th>Benchmark</th><th>Present</th><th>Missing</th><th>Disagreement</th><th>Review</th></tr>'
        + "".join(rows) + "</table>"
    )
    write_html(path, "Pre-content A/B test", body)


def _write_workbook(path: Path, cases: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)
    sheets = {name: workbook.create_sheet(name) for name in (
        "SUMMARY", "CASE_COMPARE", "HYBRID_FIELDS", "LLM_ONLY_FIELDS", "CONFLICTS",
        "MISSING_FIELDS", "NEEDS_REVIEW", "EVIDENCE", "DOC_ROUTER",
    )}
    sheets["SUMMARY"].append(["METRIC", "VALUE"])
    for key, value in summary.items():
        if key != "cases":
            sheets["SUMMARY"].append([key, _display(value)])
    for name in ("CASE_COMPARE", "HYBRID_FIELDS", "LLM_ONLY_FIELDS", "CONFLICTS", "MISSING_FIELDS", "NEEDS_REVIEW", "EVIDENCE"):
        sheets[name].append(["CASE_ID", "FIELD", "VALUE", "STATUS", "DETAIL"])
    sheets["DOC_ROUTER"].append(["CASE_ID", "DOCUMENT_TYPE", "BENCHMARK_INCLUDED", "WARNINGS"])
    for case in cases:
        case_id = case["case_id"]
        sheets["DOC_ROUTER"].append([case_id, case["segmenter"]["document_type"], case["benchmark_included"], "; ".join(case["segmenter"]["warnings"])])
        for row in case["compare"]["fields"]:
            sheets["CASE_COMPARE"].append([case_id, row["field"], _display(row["hybrid"]), row["status"], _display(row["llm_only"])])
            if row["status"] in {"missing_both", "missing_one"}:
                sheets["MISSING_FIELDS"].append([case_id, row["field"], _display(row["hybrid"]), row["status"], _display(row["llm_only"])])
        for strategy_key, sheet_name in (("hybrid_output", "HYBRID_FIELDS"), ("llm_only_output", "LLM_ONLY_FIELDS")):
            for field, value in flatten_output(case[strategy_key]).items():
                sheets[sheet_name].append([case_id, field, _display(value), "", ""])
        for conflict in case["hybrid_output"].get("conflicts", []):
            sheets["CONFLICTS"].append([case_id, conflict.get("field"), _display(conflict.get("kept_value")), "conflict", _display(conflict)])
        for strategy_key in ("hybrid_output", "llm_only_output"):
            if case[strategy_key].get("needs_review"):
                sheets["NEEDS_REVIEW"].append([case_id, strategy_key, "", "needs_review", "; ".join(case[strategy_key].get("warnings", []))])
            for evidence in case[strategy_key].get("evidence", []):
                sheets["EVIDENCE"].append([case_id, evidence.get("field"), evidence.get("value"), strategy_key, _display(evidence)])
    workbook.save(path)


def _skipped_output(segment: dict[str, Any], reason: str) -> dict[str, Any]:
    from court_ocr_extract.extractors.pre_content_schema import empty_pre_content_output

    output = empty_pre_content_output(str(segment.get("document_type") or "unknown"))
    output.update({"warnings": [reason], "needs_review": True, "llm_json_valid": False, "skipped": True})
    return output


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _display(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "" if value is None else str(value)


def _evidence_table(output: dict[str, Any], strategy: str) -> str:
    rows = []
    for item in output.get("evidence", []):
        line_id = str(item.get("line_id") or "")
        link = f'<a href="#{escape(line_id)}">{escape(line_id)}</a>' if line_id else ""
        rows.append(
            f'<tr><td>{escape(strategy)}</td><td>{escape(item.get("field"))}</td>'
            f'<td>{escape(item.get("value"))}</td><td>{link}</td><td>{escape(item.get("text"))}</td></tr>'
        )
    return (
        '<table><tr><th>Strategy</th><th>Field</th><th>Value</th><th>Source line</th><th>Evidence text</th></tr>'
        + "".join(rows) + "</table>"
    )
