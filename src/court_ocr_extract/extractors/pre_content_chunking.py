from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable

from court_ocr_extract.extractors.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extractors.pre_content_schema import empty_pre_content_output, normalize_pre_content_output
from court_ocr_extract.local_llm import LocalLLMBudget, classify_llm_error


LLMCallable = Callable[[str, str], dict[str, Any]]


@dataclass(frozen=True)
class PreContentChunk:
    name: str
    target: str
    lines: list[dict[str, Any]]


PANEL_MARKERS = (
    "thanh phan hoi dong xet xu",
    "tham phan",
    "hoi tham nhan dan",
    "thu ky phien toa",
    "dai dien vien kiem sat",
    "kiem sat vien",
)
PARTICIPANT_MARKERS = (
    "bi hai",
    "nguoi co quyen loi",
    "nguoi lam chung",
    "nguoi dai dien",
)


def build_pre_content_chunks(segment: dict[str, Any], settings: Any) -> list[PreContentChunk]:
    lines = [dict(line) for line in segment.get("pre_content_lines", []) if line.get("text")]
    if not lines:
        return []
    limit = max(10, int(getattr(settings, "local_llm_chunk_lines", 80)))
    overlap = max(0, min(limit - 1, int(getattr(settings, "local_llm_chunk_overlap_lines", 10))))
    chunks = [PreContentChunk("document_metadata", "document_metadata", lines[:limit])]

    panel_indexes = _matching_indexes(lines, PANEL_MARKERS)
    if panel_indexes:
        chunks.extend(_window_chunks("trial_panel", "trial_panel", lines, panel_indexes, limit, overlap))
    else:
        chunks.append(PreContentChunk("trial_panel_001", "trial_panel", lines[:limit]))

    defendant_starts = []
    for index, line in enumerate(lines):
        folded = _fold(str(line.get("text") or ""))
        if "doi voi bi cao" in folded or re.match(r"^\s*(?:\d+[.)]\s*)?(?:bi cao|ho va ten)\b", folded):
            defendant_starts.append(index)
    defendant_starts = list(dict.fromkeys(defendant_starts))
    for index, start in enumerate(defendant_starts):
        end = defendant_starts[index + 1] if index + 1 < len(defendant_starts) else min(len(lines), start + limit)
        block = lines[start:max(start + 1, min(end, start + limit))]
        chunks.append(PreContentChunk(f"defendant_{index + 1:03d}", "defendants", block))
    if not defendant_starts:
        chunks.append(PreContentChunk("defendant_001", "defendants", lines[:limit]))

    participant_indexes = _matching_indexes(lines, PARTICIPANT_MARKERS)
    if participant_indexes:
        chunks.extend(
            _window_chunks("participants", "participants", lines, participant_indexes, limit, overlap)
        )
    else:
        chunks.append(PreContentChunk("participants_001", "participants", lines[:limit]))
    return _unique_chunks(chunks)


def extract_pre_content_chunks(
    segment: dict[str, Any],
    *,
    settings: Any,
    prompt: str,
    strategy: str,
    llm_callable: LLMCallable | None = None,
) -> dict[str, Any]:
    document_type = str(segment.get("document_type") or "unknown")
    chunks = build_pre_content_chunks(segment, settings)
    statuses: list[dict[str, Any]] = []
    successful: list[tuple[PreContentChunk, dict[str, Any]]] = []
    warnings: list[str] = []
    extractor = LocalLLMExtractor(settings)

    for chunk in chunks:
        request_text = json.dumps(
            {
                "scope": "pre_content_only",
                "chunk_name": chunk.name,
                "target": chunk.target,
                "document_type": document_type,
                "lines": chunk.lines,
            },
            ensure_ascii=False,
        )
        chunk_prompt = (
            prompt
            + f"\n\nCHUNK {chunk.name}: chỉ trả dữ liệu cho nhóm {chunk.target}; "
            "các nhóm khác để rỗng và không suy diễn ngoài các dòng INPUT."
        )
        try:
            if llm_callable is not None:
                payload, chunk_statuses = _call_fake_with_status(
                    llm_callable,
                    prompt=chunk_prompt,
                    text=request_text,
                    chunk=chunk,
                    settings=settings,
                )
            else:
                payload, chunk_statuses = extractor.call_json_prompt_with_status(
                    prompt=chunk_prompt,
                    text=request_text,
                    chunk_name=chunk.name,
                    chunked=True,
                )
            for item in chunk_statuses:
                item.update(strategy=strategy, llm_required=strategy == "llm_only")
            statuses.extend(chunk_statuses)
            successful.append(
                (chunk, normalize_pre_content_output(payload, document_type=document_type))
            )
        except Exception as exc:
            chunk_statuses = extractor.last_request_statuses
            if not chunk_statuses:
                chunk_statuses = [_failed_status(chunk, settings, exc)]
            for item in chunk_statuses:
                item.update(strategy=strategy, llm_required=strategy == "llm_only")
            statuses.extend(chunk_statuses)
            warnings.append(f"llm_chunk_failed:{chunk.name}:{classify_llm_error(exc)}")

    if not successful:
        return {
            "document_type": document_type,
            "status": "llm_only_failed" if strategy == "llm_only" else "hybrid_llm_failed",
            "result_valid": False,
            "llm_json_valid": False,
            "llm_actually_called": any(item.get("llm_actually_called") for item in statuses),
            "chunk_count": len(chunks),
            "llm_status": statuses,
            "warnings": warnings or ["llm_no_chunks_available"],
            "needs_review": True,
        }

    output = empty_pre_content_output(document_type)
    for chunk, payload in successful:
        _merge_chunk(output, payload, chunk.target)
    output["warnings"].extend(warnings)
    output["status"] = (
        "llm_only_succeeded" if len(successful) == len(chunks) else "llm_only_partial"
    ) if strategy == "llm_only" else (
        "hybrid_llm_succeeded" if len(successful) == len(chunks) else "hybrid_llm_partial"
    )
    output["result_valid"] = True
    output["llm_json_valid"] = True
    output["llm_actually_called"] = any(item.get("llm_actually_called") for item in statuses)
    output["chunk_count"] = len(chunks)
    output["llm_status"] = statuses
    output["needs_review"] = bool(output["needs_review"] or warnings)
    return output


def _merge_chunk(output: dict[str, Any], payload: dict[str, Any], target: str) -> None:
    if target == "document_metadata":
        for key, value in payload.get("metadata", {}).items():
            if output["metadata"].get(key) in (None, "", []) and value not in (None, "", []):
                output["metadata"][key] = value
    elif target == "trial_panel":
        for key, value in payload.get("trial_panel", {}).items():
            if output["trial_panel"].get(key) in (None, "", []) and value not in (None, "", []):
                output["trial_panel"][key] = value
    elif target == "defendants":
        output["defendants"].extend(payload.get("defendants", []))
        output["defendants"] = _dedupe_entities(output["defendants"], role_key=None)
    elif target == "participants":
        output["participants"].extend(payload.get("participants", []))
        output["participants"] = _dedupe_entities(output["participants"], role_key="role")
    output["evidence"].extend(
        item for item in payload.get("evidence", []) if item not in output["evidence"]
    )
    output["warnings"].extend(
        item for item in payload.get("warnings", []) if item not in output["warnings"]
    )


def _dedupe_entities(items: list[dict[str, Any]], role_key: str | None) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for item in items:
        key = (
            _fold(str(item.get("full_name") or "")),
            _fold(str(item.get(role_key) or "")) if role_key else "",
            tuple(sorted(str(value) for value in item.get("evidence_line_ids", []))),
        )
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _call_fake_with_status(llm_callable, *, prompt, text, chunk, settings):
    started = time.perf_counter()
    budget = LocalLLMBudget.from_settings(settings)
    prepared, meta = budget.prepare(system_prompt=prompt, user_content=text, chunked=True)
    payload = llm_callable(prompt, prepared)
    status = _base_status(chunk, settings)
    status.update(meta)
    status.update(
        llm_actually_called=True,
        request_ok=True,
        response_ok=True,
        duration_ms=round((time.perf_counter() - started) * 1000, 3),
    )
    return payload, [status]


def _failed_status(chunk: PreContentChunk, settings: Any, exc: Exception) -> dict[str, Any]:
    status = _base_status(chunk, settings)
    status.update(error_type=classify_llm_error(exc), error_message=str(exc))
    return status


def _base_status(chunk: PreContentChunk, settings: Any) -> dict[str, Any]:
    budget = LocalLLMBudget.from_settings(settings)
    return {
        "strategy": "",
        "chunk_name": chunk.name,
        "llm_required": False,
        "llm_available": True,
        "llm_actually_called": False,
        "provider": str(getattr(settings, "local_llm_provider", "vllm")),
        "model": str(getattr(settings, "local_llm_model_name", "")),
        "base_url": str(getattr(settings, "local_llm_base_url", "")),
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
    }


def _matching_indexes(lines: list[dict[str, Any]], markers: tuple[str, ...]) -> list[int]:
    return [
        index
        for index, line in enumerate(lines)
        if any(marker in _fold(str(line.get("text") or "")) for marker in markers)
    ]


def _window_chunks(prefix, target, lines, indexes, limit, overlap):
    chunks = []
    for number, index in enumerate(_dedupe_close(indexes), start=1):
        before = min(10, overlap)
        start = max(0, index - before)
        chunks.append(
            PreContentChunk(f"{prefix}_{number:03d}", target, lines[start : start + limit])
        )
    return chunks


def _dedupe_close(indexes: list[int], distance: int = 4) -> list[int]:
    result = []
    for index in indexes:
        if not result or index - result[-1] > distance:
            result.append(index)
    return result


def _unique_chunks(chunks: list[PreContentChunk]) -> list[PreContentChunk]:
    result = []
    seen = set()
    for chunk in chunks:
        signature = (chunk.target, tuple(str(line.get("line_id")) for line in chunk.lines))
        if signature not in seen:
            seen.add(signature)
            result.append(chunk)
    return result


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower().replace("đ", "d"))
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char)).split()
    )
