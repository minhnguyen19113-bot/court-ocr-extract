from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from court_ocr_extract.extractors.llm_only_pre_content_extractor import LLMCallable
from court_ocr_extract.extractors.pre_content_chunking import extract_pre_content_chunks
from court_ocr_extract.extractors.pre_content_schema import (
    DEFENDANT_FIELDS,
    METADATA_FIELDS,
    PARTICIPANT_FIELDS,
    TRIAL_PANEL_FIELDS,
    unresolved_field_paths,
)
from court_ocr_extract.extractors.rule_based_pre_content_extractor import extract_pre_content_rules
from court_ocr_extract.settings import PipelineSettings


class HybridPreContentExtractor:
    name = "hybrid_rule_llm"

    def __init__(self, settings: PipelineSettings, *, llm_callable: LLMCallable | None = None) -> None:
        self.settings = settings
        self._llm_callable = llm_callable

    def extract(self, segment: dict[str, Any], *, case_id: str) -> dict[str, Any]:
        rule_output = extract_pre_content_rules(segment)
        unresolved = unresolved_field_paths(rule_output)
        try:
            repair = extract_pre_content_chunks(
                segment,
                settings=self.settings,
                prompt=_load_prompt()
                + "\n\nCác field chưa giải quyết: "
                + ", ".join(unresolved),
                strategy=self.name,
                llm_callable=self._llm_callable,
            )
            if repair.get("result_valid"):
                merged = merge_rule_and_llm(rule_output, repair)
            else:
                merged = deepcopy(rule_output)
                merged["warnings"].extend(repair.get("warnings", []))
            merged["llm_json_valid"] = bool(repair.get("result_valid"))
            merged["result_valid"] = True
            merged["status"] = (
                "hybrid_succeeded" if repair.get("result_valid") else "hybrid_rule_only_fallback"
            )
            merged["llm_status"] = repair.get("llm_status", [])
            merged["llm_actually_called"] = bool(repair.get("llm_actually_called"))
            merged["chunk_count"] = int(repair.get("chunk_count", 0))
        except Exception as exc:
            merged = deepcopy(rule_output)
            merged["warnings"].append(f"hybrid_llm_repair_failed:{type(exc).__name__}:{exc}")
            merged["needs_review"] = True
            merged["llm_json_valid"] = False
            merged["result_valid"] = True
            merged["status"] = "hybrid_rule_only_fallback"
            merged["llm_status"] = []
            merged["llm_actually_called"] = False
            merged["chunk_count"] = 0
        merged["rule_output"] = rule_output
        merged["unresolved_fields"] = unresolved
        merged["case_id"] = case_id
        return merged


def merge_rule_and_llm(rule: dict[str, Any], llm: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(rule)
    merged.setdefault("conflicts", [])
    for group, fields in (("metadata", METADATA_FIELDS), ("trial_panel", TRIAL_PANEL_FIELDS)):
        for field in fields:
            path = f"{group}.{field}"
            rule_value = merged[group].get(field)
            llm_value = llm.get(group, {}).get(field)
            if _missing(rule_value) and not _missing(llm_value):
                merged[group][field] = deepcopy(llm_value)
                merged["field_meta"][path] = {"source": "llm_repair", "confidence": None, "evidence_line_ids": _llm_evidence(llm, path)}
            elif not _missing(rule_value) and not _missing(llm_value) and rule_value != llm_value:
                _conflict(merged, path, rule_value, llm_value, llm)
    _merge_entities(merged, llm, "defendants", DEFENDANT_FIELDS)
    _merge_entities(merged, llm, "participants", PARTICIPANT_FIELDS)
    merged["evidence"].extend(item for item in llm.get("evidence", []) if item not in merged["evidence"])
    merged["warnings"].extend(item for item in llm.get("warnings", []) if item not in merged["warnings"])
    if merged["conflicts"]:
        merged["warnings"].append("hybrid_rule_llm_conflict")
        merged["needs_review"] = True
    return merged


def _merge_entities(merged: dict[str, Any], llm: dict[str, Any], key: str, fields: tuple[str, ...]) -> None:
    candidates = llm.get(key, [])
    if not merged[key] and candidates:
        merged[key] = deepcopy(candidates)
        return
    for index, item in enumerate(candidates):
        if index >= len(merged[key]):
            merged[key].append(deepcopy(item))
            continue
        for field in fields:
            rule_value = merged[key][index].get(field)
            llm_value = item.get(field)
            path = f"{key}[{index}].{field}"
            if _missing(rule_value) and not _missing(llm_value):
                merged[key][index][field] = deepcopy(llm_value)
            elif not _missing(rule_value) and not _missing(llm_value) and rule_value != llm_value:
                _conflict(merged, path, rule_value, llm_value, llm)
                merged[key][index]["needs_review"] = True


def _conflict(merged: dict[str, Any], path: str, rule_value: Any, llm_value: Any, llm: dict[str, Any]) -> None:
    merged["conflicts"].append({
        "field": path,
        "rule_value": rule_value,
        "llm_value": llm_value,
        "kept_value": rule_value,
        "evidence_line_ids": _llm_evidence(llm, path),
    })


def _llm_evidence(llm: dict[str, Any], path: str) -> list[str]:
    return [
        str(item.get("line_id")) for item in llm.get("evidence", [])
        if item.get("field") == path and item.get("line_id")
    ]


def _missing(value: Any) -> bool:
    return value in (None, "", [])


def _load_prompt() -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / "pre_content_hybrid_repair_prompt.vi.md"
    return path.read_text(encoding="utf-8")
