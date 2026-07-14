from __future__ import annotations

import json
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from court_ocr_extract.extractors.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extractors.pre_content_anchor_segmenter import segment_pre_content_anchors
from court_ocr_extract.extractors.pre_content_schema import (
    DEFENDANT_FIELDS,
    PARTICIPANT_FIELDS,
    empty_pre_content_output,
    normalize_pre_content_output,
)
from court_ocr_extract.extractors.rule_anchor_extractor import (
    extract_rule_anchor_output,
    validate_defendant_entity,
    validate_participant_entity,
)
from court_ocr_extract.local_llm import LocalLLMBudget, classify_llm_error
from court_ocr_extract.settings import PipelineSettings


LLMCallable = Callable[[str, str], dict[str, Any]]
RULE_ANCHOR_STRATEGIES = ("rule_anchor_only", "llm_per_block", "rule_then_llm_per_block")
PARTICIPANT_BLOCK_FIELDS = tuple(
    "relationship_or_note" if field == "relationship" else field
    for field in PARTICIPANT_FIELDS
)


def run_rule_anchor_strategy(
    segment: dict[str, Any],
    *,
    case_id: str,
    strategy: str,
    settings: PipelineSettings,
    llm_callable: LLMCallable | None = None,
) -> dict[str, Any]:
    if strategy not in RULE_ANCHOR_STRATEGIES:
        raise ValueError(f"Unsupported rule-anchor strategy: {strategy}")
    anchor = segment_pre_content_anchors(segment, case_id=case_id)
    rule_output = extract_rule_anchor_output(anchor)
    rule_output["case_id"] = case_id
    rule_output["strategy"] = strategy
    if strategy == "rule_anchor_only":
        return rule_output

    output = _entity_base(rule_output) if strategy == "llm_per_block" else deepcopy(rule_output)
    output["strategy"] = strategy
    output["llm_status"] = []
    output["warnings"] = list(output.get("warnings", []))
    llm_settings = replace(
        settings,
        local_llm_max_input_chars=min(settings.local_llm_max_input_chars, 6000),
        local_llm_max_output_tokens=min(settings.local_llm_max_output_tokens, 512),
    )
    extractor = LocalLLMExtractor(llm_settings)

    for kind, blocks in (
        ("defendants", anchor.get("defendant_blocks", [])),
        ("participants", anchor.get("participant_blocks", [])),
    ):
        rule_entities = rule_output.get(kind, [])
        output_entities = output.get(kind, [])
        for index, block in enumerate(blocks):
            rule_entity = rule_entities[index] if index < len(rule_entities) else None
            current = output_entities[index] if index < len(output_entities) else None
            if strategy == "rule_then_llm_per_block" and not _needs_repair(kind, rule_entity):
                continue
            try:
                payload, statuses = _call_block(
                    extractor,
                    llm_callable=llm_callable,
                    settings=llm_settings,
                    strategy=strategy,
                    kind=kind,
                    block=block,
                )
                output["llm_status"].extend(statuses)
                candidate = _entity_from_payload(payload, kind, block)
                if candidate is None:
                    output["warnings"].append(f"llm_block_empty:{block['block_id']}")
                    continue
                if kind == "defendants":
                    validate_defendant_entity(candidate)
                else:
                    validate_participant_entity(candidate)
                if strategy == "llm_per_block":
                    output[kind].append(candidate)
                elif current is not None:
                    _merge_missing(current, candidate, DEFENDANT_FIELDS if kind == "defendants" else PARTICIPANT_FIELDS)
            except Exception as exc:
                statuses = extractor.last_request_statuses or [
                    _failed_status(
                        strategy,
                        kind,
                        block,
                        llm_settings,
                        exc,
                        called=llm_callable is not None,
                    )
                ]
                for status in statuses:
                    status["strategy"] = strategy
                output["llm_status"].extend(statuses)
                output["warnings"].append(
                    f"llm_block_failed:{block['block_id']}:{classify_llm_error(exc)}"
                )

    output["llm_actually_called"] = any(
        status.get("llm_actually_called") for status in output["llm_status"]
    )
    output["chunk_count"] = len(output["llm_status"])
    successful_calls = sum(bool(status.get("response_ok")) for status in output["llm_status"])
    has_entity_blocks = bool(anchor.get("defendant_blocks") or anchor.get("participant_blocks"))
    output["llm_json_valid"] = successful_calls > 0
    output["result_valid"] = strategy == "rule_then_llm_per_block" or (
        successful_calls > 0 or not has_entity_blocks
    )
    output["status"] = _strategy_status(strategy, output["llm_status"])
    output["needs_review"] = bool(
        output["warnings"]
        or any(entity.get("needs_review") for entity in output["defendants"] + output["participants"])
    )
    output["anchor_segments"] = anchor
    return output


def _entity_base(rule_output: dict[str, Any]) -> dict[str, Any]:
    output = empty_pre_content_output(str(rule_output.get("document_type") or "unknown"))
    output["metadata"] = deepcopy(rule_output["metadata"])
    output["trial_panel"] = deepcopy(rule_output["trial_panel"])
    output["evidence"] = deepcopy(rule_output.get("evidence", []))
    output["field_meta"] = deepcopy(rule_output.get("field_meta", {}))
    output["warnings"] = list(rule_output.get("warnings", []))
    output["anchor_segments"] = deepcopy(rule_output.get("anchor_segments", {}))
    return output


def _needs_repair(kind: str, entity: dict[str, Any] | None) -> bool:
    if entity is None or entity.get("needs_review") or entity.get("warnings"):
        return True
    if kind == "defendants":
        core = ("full_name", "birth_date_or_year", "permanent_address", "occupation", "detention_status")
        return sum(entity.get(field) in (None, "") for field in core) >= 3
    return any(entity.get(field) in (None, "") for field in ("role", "full_name", "address"))


def _call_block(extractor, *, llm_callable, settings, strategy, kind, block):
    prompt = _load_block_prompt()
    request = {
        "block_id": block["block_id"],
        "type": "defendant" if kind == "defendants" else "participant",
        "role_hint": block.get("role_hint"),
        "line_ids": block.get("line_ids", []),
        "raw_lines": _bounded_lines(str(block.get("text") or ""), 4400),
        "expected_schema": list(DEFENDANT_FIELDS if kind == "defendants" else PARTICIPANT_BLOCK_FIELDS),
    }
    text = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
    if llm_callable is None:
        payload, statuses = extractor.call_json_prompt_with_status(
            prompt=prompt,
            text=text,
            chunk_name=block["block_id"],
            chunked=True,
        )
    else:
        started = time.perf_counter()
        budget = LocalLLMBudget.from_settings(settings)
        prepared, metadata = budget.prepare(system_prompt=prompt, user_content=text, chunked=True)
        payload = llm_callable(prompt, prepared)
        status = _status_base(strategy, kind, block, settings)
        status.update(metadata)
        status.update(
            llm_actually_called=True,
            request_ok=True,
            response_ok=True,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
        )
        statuses = [status]
    for status in statuses:
        status.update(strategy=strategy, llm_required=True)
    return payload, statuses


def _entity_from_payload(payload: dict[str, Any], kind: str, block: dict[str, Any]) -> dict[str, Any] | None:
    payload = _participant_relationship_alias(payload, kind)
    if kind in payload and isinstance(payload.get(kind), list):
        normalized = normalize_pre_content_output(payload)
        values = normalized[kind]
        entity = values[0] if values else None
    elif isinstance(payload, dict):
        wrapper = {kind: [payload]}
        normalized = normalize_pre_content_output(wrapper)
        entity = normalized[kind][0] if normalized[kind] else None
    else:
        entity = None
    if entity is not None and not entity.get("evidence_line_ids"):
        entity["evidence_line_ids"] = list(block.get("line_ids", []))
    if entity is not None and not entity.get("raw_block"):
        entity["raw_block"] = str(block.get("text") or "")
    if entity is not None and kind == "participants":
        entity["relationship_or_note"] = entity.get("relationship")
    return entity


def _participant_relationship_alias(payload: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind != "participants" or not isinstance(payload, dict):
        return payload
    output = deepcopy(payload)
    values = output.get("participants") if isinstance(output.get("participants"), list) else [output]
    for value in values:
        if isinstance(value, dict) and not value.get("relationship") and value.get("relationship_or_note"):
            value["relationship"] = value["relationship_or_note"]
    return output


def _merge_missing(target: dict[str, Any], candidate: dict[str, Any], fields: tuple[str, ...]) -> None:
    repaired = []
    for field in fields:
        if target.get(field) in (None, "", []) and candidate.get(field) not in (None, "", []):
            target[field] = deepcopy(candidate[field])
            repaired.append(field)
    target["evidence_line_ids"] = list(
        dict.fromkeys(target.get("evidence_line_ids", []) + candidate.get("evidence_line_ids", []))
    )
    if "relationship" in repaired:
        target["relationship_or_note"] = target.get("relationship")
    if repaired:
        target["warnings"] = [
            warning for warning in target.get("warnings", [])
            if not (
                (warning.startswith("field_too_long:") and warning.split(":", 1)[1] in repaired)
                or (warning == "defendant_name_missing" and "full_name" in repaired)
                or (warning == "participant_name_missing" and "full_name" in repaired)
                or (warning == "participant_role_missing" and "role" in repaired)
            )
        ]
    target["needs_review"] = bool(target.get("warnings") or not target.get("full_name"))


def _strategy_status(strategy: str, statuses: list[dict[str, Any]]) -> str:
    if not statuses:
        return "rule_then_no_llm_needed" if strategy == "rule_then_llm_per_block" else "llm_per_block_no_blocks"
    successful = sum(bool(status.get("response_ok")) for status in statuses)
    if successful == len(statuses):
        return f"{strategy}_succeeded"
    if successful:
        return f"{strategy}_partial"
    return f"{strategy}_failed"


def _failed_status(strategy, kind, block, settings, exc, *, called=False):
    status = _status_base(strategy, kind, block, settings)
    status.update(
        llm_actually_called=called,
        request_ok=False,
        response_ok=False,
        error_type=classify_llm_error(exc),
        error_message=str(exc),
    )
    return status


def _status_base(strategy, kind, block, settings):
    budget = LocalLLMBudget.from_settings(settings)
    return {
        "strategy": strategy,
        "chunk_name": block["block_id"],
        "llm_required": True,
        "llm_available": True,
        "llm_actually_called": False,
        "provider": settings.local_llm_provider,
        "model": settings.local_llm_model_name,
        "base_url": settings.local_llm_base_url,
        "context_window": budget.context_window,
        "input_chars": 0,
        "estimated_input_tokens": 0,
        "max_output_tokens": budget.max_output_tokens,
        "budget_ok": False,
        "truncated": False,
        "chunked": True,
        "request_ok": False,
        "response_ok": False,
        "error_type": None,
        "error_message": None,
        "duration_ms": 0.0,
        "block_type": kind,
    }


def _bounded_lines(text: str, max_chars: int) -> list[str]:
    output = []
    total = 0
    for line in text.splitlines():
        remaining = max_chars - total
        if remaining <= 0:
            break
        value = line[:remaining]
        output.append(value)
        total += len(value)
    return output


def _load_block_prompt() -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / "pre_content_per_block_prompt.vi.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Chỉ trích xuất JSON cho một block pre-content và giữ evidence_line_ids."
