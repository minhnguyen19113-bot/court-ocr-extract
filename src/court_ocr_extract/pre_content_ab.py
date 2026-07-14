from __future__ import annotations

import json
from copy import deepcopy
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

CASES_HEADERS = (
    "case_id", "source_file", "document_type", "ocr_status", "marker_found", "marker_page",
    "early_stop_triggered", "pages_processed", "pages_total", "strategy_used", "court_name",
    "judgment_number", "judgment_date", "case_acceptance_number", "trial_decision_number",
    "postponement_decision_number", "trial_date_or_location_sentence", "presiding_judge", "clerk",
    "prosecutor", "needs_review", "warnings",
)
DEFENDANTS_HEADERS = (
    "case_id", "defendant_index", "full_name", "alias", "birth_date_or_year", "birth_place",
    "permanent_address", "current_address", "detention_status", "presence_status", "occupation",
    "education", "nationality", "ethnicity", "religion", "gender", "father_name", "mother_name",
    "spouse", "children", "criminal_record", "evidence_line_ids", "evidence_text", "needs_review",
    "warnings",
)
PARTICIPANTS_HEADERS = (
    "case_id", "participant_index", "role", "full_name", "birth_date_or_year", "address",
    "presence_status", "relationship_or_note", "evidence_line_ids", "evidence_text", "needs_review",
    "warnings",
)
TRIAL_PANEL_HEADERS = (
    "case_id", "role", "name", "title_or_position", "organization", "evidence_line_ids",
    "evidence_text", "warnings",
)
LLM_STATUS_HEADERS = (
    "case_id", "strategy", "chunk_name", "llm_required", "llm_available",
    "llm_actually_called", "provider", "model", "base_url", "context_window", "input_chars",
    "input_tokens_estimated", "max_output_tokens", "budget_ok", "truncated", "chunked",
    "request_ok", "response_ok", "error_type", "error_message", "duration_ms",
)


def run_pre_content_ab_test(
    records: list[OCRCacheRecord],
    *,
    output_dir: str | Path,
    settings: PipelineSettings,
    strategies: list[str] | None = None,
    limit: int | None = None,
    llm_callable: LLMCallable | None = None,
    llm_preflight: dict[str, Any] | None = None,
    llm_available: bool | None = None,
) -> dict[str, Any]:
    selected = records[:limit] if limit is not None else records
    requested = strategies or list(STRATEGIES)
    unknown = [name for name in requested if name not in STRATEGIES]
    if unknown:
        raise ValueError(f"Unsupported pre-content strategies: {', '.join(unknown)}")
    available = True if llm_available is None else llm_available
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
        hybrid_output = None
        llm_output = None
        if correction:
            hybrid_output = _skipped_output(segment, "correction_notice_not_in_judgment_benchmark")
            llm_output = _skipped_output(segment, "correction_notice_not_in_judgment_benchmark")
        elif not available:
            if "hybrid_rule_llm" in requested:
                hybrid_output = _hybrid_without_llm(rule, llm_preflight)
            if "llm_only" in requested:
                llm_output = _llm_unavailable_output(segment, llm_preflight)
        else:
            if "hybrid_rule_llm" in requested:
                hybrid_output = hybrid.extract(segment, case_id=record.case_id)
            if "llm_only" in requested:
                llm_output = llm_only.extract(segment, case_id=record.case_id)
        hybrid_output = hybrid_output or _skipped_output(segment, "strategy_not_requested")
        llm_output = llm_output or _skipped_output(segment, "strategy_not_requested")
        compare = compare_outputs(hybrid_output, llm_output)
        metrics = _case_metrics(segment, hybrid_output, llm_output, compare)
        case = {
            "case_id": record.case_id,
            "segmenter": segment,
            "ocr": _ocr_summary(record),
            "rule_output": rule,
            "hybrid_output": hybrid_output,
            "llm_only_output": llm_output,
            "compare": compare,
            "metrics": metrics,
            "benchmark_included": not correction and segment["document_type"] == "judgment_criminal_first_instance",
        }
        _write_case(case_dir, case)
        cases.append(case)
    summary = _summary(cases, requested, llm_preflight)
    _write_json(output_dir / "compare_summary.json", summary)
    _write_workbook(output_dir / "compare_summary.xlsx", cases, summary)
    _write_index(output_dir / "index.html", cases, llm_preflight)
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
    present = [field for field, value in hybrid_flat.items() if value not in (None, "", [])]
    evidence_fields = {item.get("field") for item in hybrid.get("evidence", []) if item.get("field")}
    statuses = hybrid.get("llm_status", []) + llm_only.get("llm_status", [])
    return {
        "field_present_count": len(present),
        "field_missing_count": sum(value in (None, "", []) for value in hybrid_flat.values()),
        "conflict_count": len(hybrid.get("conflicts", [])),
        "needs_review_count": int(bool(hybrid.get("needs_review"))) + int(bool(llm_only.get("needs_review"))),
        "evidence_coverage_rate": round(len(evidence_fields & set(present)) / max(1, len(present)), 4),
        "participant_count": len(hybrid.get("participants", [])),
        "defendant_count": len(hybrid.get("defendants", [])),
        "document_type_detected": segment.get("document_type"),
        "segment_stop_found": bool(segment.get("stop_line_id")),
        "llm_json_valid": bool(llm_only.get("llm_json_valid", False)),
        "llm_only_status": llm_only.get("status", "unknown"),
        "llm_actually_called": any(item.get("llm_actually_called") for item in statuses),
        "llm_chunk_count": len(statuses),
        "llm_chunk_error_count": sum(bool(item.get("error_type")) for item in statuses),
        "hybrid_vs_llm_disagreement_count": compare["disagreement_count"],
    }


def _summary(cases, strategies, llm_preflight):
    return {
        "task": "pre_content_extraction_ab_test",
        "strategies": strategies,
        "llm_preflight": llm_preflight,
        "case_count": len(cases),
        "judgment_benchmark_count": sum(case["benchmark_included"] for case in cases),
        "correction_notice_count": sum(case["segmenter"]["document_type"] == "correction_notice" for case in cases),
        "unknown_document_count": sum(case["segmenter"]["document_type"] == "unknown" for case in cases),
        "totals": {
            key: sum(case["metrics"].get(key, 0) for case in cases)
            for key in (
                "field_present_count", "field_missing_count", "conflict_count", "needs_review_count",
                "participant_count", "defendant_count", "llm_chunk_count", "llm_chunk_error_count",
                "hybrid_vs_llm_disagreement_count",
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
    compare_rows = "".join(
        f'<tr><td>{escape(item["field"])}</td><td>{escape(_display(item["hybrid"]))}</td>'
        f'<td>{escape(_display(item["llm_only"]))}</td><td>{escape(item["status"])}</td></tr>'
        for item in case["compare"]["fields"]
    )
    source_lines = "".join(
        f'<div id="{escape(line.get("line_id"))}"><code>{escape(line.get("line_id"))}</code> '
        f'{escape(line.get("text"))}</div>'
        for line in case["segmenter"].get("pre_content_lines", [])
    )
    llm_output = case["llm_only_output"]
    llm_panel = (
        f'<pre>{escape(_display(llm_output))}</pre>'
        if llm_output.get("result_valid")
        else f'<p><strong>Không có output LLM-only hợp lệ.</strong> Status: {escape(llm_output.get("status"))}</p>'
    )
    body = (
        f'<h1>{escape(case["case_id"])}</h1>'
        + _llm_runtime_html(case)
        + '<div class="grid"><section><h2>Văn bản pre-content</h2>'
        + f'<div>{source_lines}</div></section>'
        + f'<section><h2>Hybrid</h2><pre>{escape(_display(case["hybrid_output"]))}</pre></section>'
        + f'<section><h2>LLM-only</h2>{llm_panel}</section></div>'
        + '<h2>So sánh field</h2><table><tr><th>Field</th><th>Hybrid</th><th>LLM-only</th><th>Status</th></tr>'
        + compare_rows + '</table><h2>Evidence</h2>'
        + _evidence_table(case["hybrid_output"], "hybrid")
        + _evidence_table(case["llm_only_output"], "llm_only")
    )
    write_html(path, "Pre-content A/B review", body)


def _llm_runtime_html(case: dict[str, Any]) -> str:
    statuses = case["hybrid_output"].get("llm_status", []) + case["llm_only_output"].get("llm_status", [])
    rows = "".join(
        f'<tr><td>{escape(item.get("strategy"))}</td><td>{escape(item.get("chunk_name"))}</td>'
        f'<td>{escape(item.get("model"))}</td><td>{escape(item.get("base_url"))}</td>'
        f'<td>{escape(item.get("context_window"))}</td><td>{escape(item.get("estimated_input_tokens"))}</td>'
        f'<td>{escape(item.get("llm_actually_called"))}</td><td>{escape(item.get("error_type"))}</td></tr>'
        for item in statuses
    )
    return (
        '<section><h2>Trạng thái Local LLM</h2><table><tr><th>Strategy</th><th>Chunk</th>'
        '<th>Model</th><th>Base URL</th><th>Context</th><th>Input token ước lượng</th>'
        '<th>Đã gọi</th><th>Lỗi</th></tr>' + rows + '</table></section>'
    )


def _write_index(path: Path, cases: list[dict[str, Any]], preflight: dict[str, Any] | None) -> None:
    runtime = preflight or {"ok": "not_run", "model": "", "base_url": ""}
    rows = "".join(
        f'<tr><td><a href="cases/{escape(case["case_id"])}/review.html">{escape(case["case_id"])}</a></td>'
        f'<td>{escape(case["metrics"]["document_type_detected"])}</td><td>{escape(case["metrics"]["llm_only_status"])}</td>'
        f'<td>{escape(case["metrics"]["llm_actually_called"])}</td><td>{escape(case["metrics"]["llm_chunk_count"])}</td>'
        f'<td>{escape(case["metrics"]["llm_chunk_error_count"])}</td></tr>'
        for case in cases
    )
    body = (
        '<h1>So sánh extraction pre-content</h1>'
        f'<p>LLM preflight: <strong>{escape(runtime.get("ok"))}</strong>; model: {escape(runtime.get("model"))}; '
        f'base URL: {escape(runtime.get("base_url"))}</p>'
        '<table><tr><th>Case</th><th>Document type</th><th>LLM-only status</th><th>Đã gọi LLM</th>'
        '<th>Số chunk</th><th>Chunk lỗi</th></tr>' + rows + '</table>'
    )
    write_html(path, "Pre-content A/B test", body)


def _write_workbook(path: Path, cases: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)
    sheet_names = (
        "SUMMARY", "CASES", "DEFENDANTS", "PARTICIPANTS", "TRIAL_PANEL", "LLM_STATUS",
        "FIELD_LONG", "EVIDENCE_LINES", "RAW_JSON", "CASE_COMPARE", "CONFLICTS",
        "MISSING_FIELDS", "NEEDS_REVIEW", "DOC_ROUTER",
    )
    sheets = {name: workbook.create_sheet(name) for name in sheet_names}
    sheets["SUMMARY"].append(["METRIC", "VALUE"])
    for key, value in summary.items():
        if key != "cases":
            sheets["SUMMARY"].append([key, _display(value)])
    for name, headers in (
        ("CASES", CASES_HEADERS), ("DEFENDANTS", DEFENDANTS_HEADERS),
        ("PARTICIPANTS", PARTICIPANTS_HEADERS), ("TRIAL_PANEL", TRIAL_PANEL_HEADERS),
        ("LLM_STATUS", LLM_STATUS_HEADERS),
    ):
        sheets[name].append(list(headers))
    sheets["FIELD_LONG"].append(["case_id", "strategy", "field", "value"])
    sheets["EVIDENCE_LINES"].append(["case_id", "strategy", "field", "value", "line_id", "text"])
    sheets["RAW_JSON"].append(["case_id", "strategy", "json"])
    sheets["CASE_COMPARE"].append(["case_id", "field", "hybrid", "status", "llm_only"])
    sheets["CONFLICTS"].append(["case_id", "field", "kept_value", "detail"])
    sheets["MISSING_FIELDS"].append(["case_id", "field", "hybrid", "llm_only"])
    sheets["NEEDS_REVIEW"].append(["case_id", "strategy", "warnings"])
    sheets["DOC_ROUTER"].append(["case_id", "document_type", "benchmark_included", "warnings"])

    for case in cases:
        _append_structured_rows(sheets, case)
        case_id = case["case_id"]
        sheets["DOC_ROUTER"].append([case_id, case["segmenter"]["document_type"], case["benchmark_included"], "; ".join(case["segmenter"]["warnings"])])
        for row in case["compare"]["fields"]:
            sheets["CASE_COMPARE"].append([case_id, row["field"], _display(row["hybrid"]), row["status"], _display(row["llm_only"])])
            if row["status"] in {"missing_both", "missing_one"}:
                sheets["MISSING_FIELDS"].append([case_id, row["field"], _display(row["hybrid"]), _display(row["llm_only"])])
        for conflict in case["hybrid_output"].get("conflicts", []):
            sheets["CONFLICTS"].append([case_id, conflict.get("field"), _display(conflict.get("kept_value")), _display(conflict)])
    workbook.save(path)


def _append_structured_rows(sheets, case):
    case_id = case["case_id"]
    line_text = {str(line.get("line_id")): str(line.get("text") or "") for line in case["segmenter"].get("pre_content_lines", [])}
    for strategy, output in (("hybrid_rule_llm", case["hybrid_output"]), ("llm_only", case["llm_only_output"])):
        metadata = output.get("metadata", {})
        panel = output.get("trial_panel", {})
        ocr = case["ocr"]
        cases_row = {
            "case_id": case_id, "source_file": ocr["source_file"], "document_type": output.get("document_type"),
            "ocr_status": ocr["ocr_status"], "marker_found": ocr["marker_found"], "marker_page": ocr["marker_page"],
            "early_stop_triggered": ocr["early_stop_triggered"], "pages_processed": ocr["pages_processed"],
            "pages_total": ocr["pages_total"], "strategy_used": strategy, **metadata,
            "trial_date_or_location_sentence": metadata.get("trial_location_or_date_sentence"),
            "presiding_judge": panel.get("presiding_judge"), "clerk": panel.get("clerk"),
            "prosecutor": panel.get("prosecutor"), "needs_review": output.get("needs_review"),
            "warnings": "; ".join(output.get("warnings", [])),
        }
        sheets["CASES"].append([cases_row.get(header) for header in CASES_HEADERS])
        for index, item in enumerate(output.get("defendants", []), start=1):
            row = {"case_id": case_id, "defendant_index": index, **item}
            row["evidence_line_ids"] = "; ".join(item.get("evidence_line_ids", []))
            row["evidence_text"] = _evidence_text(item, line_text)
            row["warnings"] = "; ".join(item.get("warnings", []))
            sheets["DEFENDANTS"].append([row.get(header) for header in DEFENDANTS_HEADERS])
        for index, item in enumerate(output.get("participants", []), start=1):
            row = {"case_id": case_id, "participant_index": index, **item}
            row["relationship_or_note"] = item.get("relationship")
            row["evidence_line_ids"] = "; ".join(item.get("evidence_line_ids", []))
            row["evidence_text"] = _evidence_text(item, line_text)
            row["warnings"] = "; ".join(item.get("warnings", []))
            sheets["PARTICIPANTS"].append([row.get(header) for header in PARTICIPANTS_HEADERS])
        _append_trial_panel(sheets["TRIAL_PANEL"], case_id, panel)
        for status in output.get("llm_status", []):
            row = {"case_id": case_id, **status}
            row["input_tokens_estimated"] = status.get("estimated_input_tokens")
            sheets["LLM_STATUS"].append([row.get(header) for header in LLM_STATUS_HEADERS])
        for field, value in flatten_output(output).items():
            sheets["FIELD_LONG"].append([case_id, strategy, field, _display(value)])
        for evidence in output.get("evidence", []):
            sheets["EVIDENCE_LINES"].append([case_id, strategy, evidence.get("field"), evidence.get("value"), evidence.get("line_id"), evidence.get("text")])
        sheets["RAW_JSON"].append([case_id, strategy, _display(output)])
        if output.get("needs_review"):
            sheets["NEEDS_REVIEW"].append([case_id, strategy, "; ".join(output.get("warnings", []))])


def _append_trial_panel(sheet, case_id, panel):
    roles = [
        ("presiding_judge", panel.get("presiding_judge")),
        *(("juror", name) for name in panel.get("jurors", [])),
        ("clerk", panel.get("clerk")),
        ("prosecutor", panel.get("prosecutor")),
    ]
    for role, name in roles:
        if name:
            sheet.append([case_id, role, name, None, None, None, None, None])


def _ocr_summary(record: OCRCacheRecord) -> dict[str, Any]:
    metadata = record.result.metadata
    marker = metadata.get("marker", {}) if isinstance(metadata.get("marker"), dict) else {}
    early_stop = metadata.get("early_stop", {}) if isinstance(metadata.get("early_stop"), dict) else {}
    return {
        "source_file": metadata.get("source_file") or record.case_id,
        "ocr_status": record.result.status,
        "marker_found": record.result.marker_found,
        "marker_page": record.result.marker_page or marker.get("page_number"),
        "early_stop_triggered": bool(early_stop.get("triggered")),
        "pages_processed": record.result.pages_processed,
        "pages_total": metadata.get("pages_total"),
    }


def _hybrid_without_llm(rule, preflight):
    output = deepcopy(rule)
    output.update(
        status="hybrid_rule_only_fallback", result_valid=True, llm_json_valid=False,
        llm_actually_called=False, chunk_count=0,
        llm_status=[_preflight_status("hybrid_rule_llm", preflight, required=False)],
    )
    output["warnings"].append("hybrid_llm_unavailable_rule_output_preserved")
    output["needs_review"] = True
    return output


def _llm_unavailable_output(segment, preflight):
    return {
        "document_type": segment.get("document_type"), "status": "llm_only_not_run",
        "result_valid": False, "llm_json_valid": False, "llm_actually_called": False,
        "chunk_count": 0, "llm_status": [_preflight_status("llm_only", preflight, required=True)],
        "warnings": ["llm_only_not_run:preflight_failed"], "needs_review": True,
    }


def _preflight_status(strategy, preflight, *, required):
    value = preflight or {}
    return {
        "strategy": strategy, "chunk_name": "preflight", "llm_required": required,
        "llm_available": False, "llm_actually_called": False, "provider": value.get("provider"),
        "model": value.get("model"), "base_url": value.get("base_url"), "context_window": None,
        "input_chars": 0, "estimated_input_tokens": 0, "max_output_tokens": None,
        "budget_ok": False, "truncated": False, "chunked": False, "request_ok": False,
        "response_ok": False, "error_type": value.get("error_type") or "llm_preflight_failed",
        "error_message": value.get("error") or "Local LLM preflight failed.", "duration_ms": 0,
    }


def _skipped_output(segment: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "document_type": str(segment.get("document_type") or "unknown"), "status": "strategy_skipped",
        "result_valid": False, "llm_json_valid": False, "llm_actually_called": False,
        "chunk_count": 0, "llm_status": [], "warnings": [reason], "needs_review": True,
        "skipped": True,
    }


def _evidence_text(item, line_text):
    return " | ".join(line_text.get(str(line_id), "") for line_id in item.get("evidence_line_ids", []) if line_text.get(str(line_id)))


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
