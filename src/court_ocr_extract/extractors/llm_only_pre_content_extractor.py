from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from court_ocr_extract.extractors.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.extractors.pre_content_schema import normalize_pre_content_output
from court_ocr_extract.settings import PipelineSettings


LLMCallable = Callable[[str, str], dict[str, Any]]


class LLMOnlyPreContentExtractor:
    name = "llm_only"

    def __init__(self, settings: PipelineSettings, *, llm_callable: LLMCallable | None = None) -> None:
        self.settings = settings
        self._llm_callable = llm_callable

    def extract(self, segment: dict[str, Any], *, case_id: str) -> dict[str, Any]:
        document_type = str(segment.get("document_type") or "unknown")
        prompt = _load_prompt("pre_content_llm_only_prompt.vi.md")
        request = _request_payload(segment, case_id=case_id)
        try:
            payload = self._call(prompt, json.dumps(request, ensure_ascii=False, indent=2))
            output = normalize_pre_content_output(payload, document_type=document_type)
            output["llm_json_valid"] = True
        except Exception as exc:
            output = normalize_pre_content_output({}, document_type=document_type)
            output["warnings"].append(f"llm_only_failed:{type(exc).__name__}:{exc}")
            output["needs_review"] = True
            output["llm_json_valid"] = False
        output["warnings"].extend(str(item) for item in segment.get("warnings", []) if item)
        return output

    def _call(self, prompt: str, text: str) -> dict[str, Any]:
        if self._llm_callable is not None:
            return self._llm_callable(prompt, text)
        return LocalLLMExtractor(self.settings).call_json_prompt(prompt=prompt, text=text)


def _request_payload(segment: dict[str, Any], *, case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "document_type": segment.get("document_type"),
        "scope": "pre_content_only",
        "lines": [
            {"line_id": line.get("line_id"), "page_number": line.get("page_number"), "text": line.get("text")}
            for line in segment.get("pre_content_lines", [])
        ],
        "pre_content_text": segment.get("pre_content_text", ""),
    }


def _load_prompt(name: str) -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / name
    return path.read_text(encoding="utf-8")
