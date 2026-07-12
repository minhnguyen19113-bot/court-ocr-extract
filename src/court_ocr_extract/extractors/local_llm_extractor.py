from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from court_ocr_extract.config import PROJECT_ROOT
from court_ocr_extract.extraction.schemas import CASE_FIELD_KEYS, PARTICIPANT_FIELD_KEYS
from court_ocr_extract.extractors.base import (
    ExtractorBackendStatus,
    normalize_extraction,
    parse_json_object,
)
from court_ocr_extract.extractors.rule_support import anchor_support_output
from court_ocr_extract.local_llm import LocalLLMClient, normalize_extraction_payload
from court_ocr_extract.local_llm.prompt_builder import load_prompt as load_legacy_prompt
from court_ocr_extract.models import ExtractorOutput, FieldValue
from court_ocr_extract.settings import PipelineSettings


class LocalLLMExtractor:
    name = "local_llm"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> ExtractorBackendStatus:
        if not self.settings.enable_local_llm_extraction:
            return ExtractorBackendStatus(self.name, False, "ENABLE_LOCAL_LLM_EXTRACTION must be true.")
        if not self.settings.local_llm_base_url:
            return ExtractorBackendStatus(self.name, False, "LOCAL_LLM_BASE_URL is required.")
        if not self.settings.local_llm_model_name:
            return ExtractorBackendStatus(self.name, False, "LOCAL_LLM_MODEL_NAME is required.")
        return ExtractorBackendStatus(self.name, True, "Local LLM configuration is present.")

    def extract_from_text(self, text: str, *, case_id: str) -> dict[str, Any]:
        status = self.check_available()
        if not status.available:
            raise RuntimeError(status.reason)
        prompt = _load_prompt() + "\n\nOCR TEXT:\n" + text
        raw = self._call_local_model(prompt)
        return normalize_extraction(parse_json_object(raw))

    def call_json_prompt(self, *, prompt: str, text: str) -> dict[str, Any]:
        """Run a task-specific prompt through the configured local model."""
        status = self.check_available()
        if not status.available:
            raise RuntimeError(status.reason)
        raw = self._call_local_model(prompt + "\n\nINPUT:\n" + text)
        try:
            return parse_json_object(raw)
        except (json.JSONDecodeError, ValueError):
            repair_path = Path(__file__).resolve().parents[3] / "prompts" / "json_repair_prompt.vi.md"
            repair_prompt = (
                repair_path.read_text(encoding="utf-8")
                if repair_path.exists()
                else "Chỉ sửa payload thành một JSON object hợp lệ, không thêm markdown."
            )
            repaired = self._call_local_model(repair_prompt + "\n\nJSON LỖI:\n" + raw)
            return parse_json_object(repaired)

    def _call_local_model(self, prompt: str) -> str:
        provider = self.settings.local_llm_provider.lower()
        if provider == "ollama":
            return self._call_ollama(prompt)
        return self._call_openai_compatible(prompt)

    def _call_ollama(self, prompt: str) -> str:
        url = self.settings.local_llm_base_url.rstrip("/") + "/api/generate"
        payload = {
            "model": self.settings.local_llm_model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.settings.local_llm_temperature},
        }
        data = _post_json(url, payload, timeout=self.settings.local_llm_timeout_seconds)
        return str(data.get("response") or "")

    def _call_openai_compatible(self, prompt: str) -> str:
        url = self.settings.local_llm_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.settings.local_llm_model_name,
            "temperature": self.settings.local_llm_temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = _post_json(url, payload, timeout=self.settings.local_llm_timeout_seconds)
        return str(data["choices"][0]["message"]["content"])


class LocalLlmExtractionError(RuntimeError):
    pass


class TypedLocalLLMExtractor:
    """Compatibility adapter for the typed legacy pipeline.

    New OCR-cache orchestration uses ``LocalLLMExtractor.extract_from_text``.
    This adapter preserves the existing ``ExtractorOutput`` contract while all
    Local LLM implementations live in the canonical extractors package.
    """

    method = "local_llm"

    def __init__(
        self,
        settings,
        prompt_path: str | Path | None = None,
        repair_prompt_path: str | Path | None = None,
    ) -> None:
        self.settings = settings
        self.prompt_path = (
            Path(prompt_path)
            if prompt_path
            else PROJECT_ROOT / "prompts" / "local_llm_extraction_prompt.txt"
        )
        self.repair_prompt_path = (
            Path(repair_prompt_path)
            if repair_prompt_path
            else PROJECT_ROOT / "prompts" / "local_llm_json_repair_prompt.txt"
        )

    def extract(self, text: str) -> ExtractorOutput:
        if not getattr(self.settings, "enable_local_llm", True):
            return ExtractorOutput(
                method=self.method,
                warnings=["Local LLM extraction is disabled."],
            )
        if getattr(self.settings, "enable_cloud_llm", False):
            raise LocalLlmExtractionError(
                "Cloud LLM extraction is disabled by design in this pipeline "
                "unless explicitly reviewed."
            )
        if (
            getattr(self.settings, "enable_mock_local_llm", False)
            or self.settings.local_llm_provider == "mock"
        ):
            return MockLocalLLMExtractor().extract(text)
        if self.settings.local_llm_provider == "remote_worker":
            return self._extract_via_remote_worker(text)

        prompt = load_legacy_prompt(
            self.prompt_path,
            "local_llm_extraction_prompt.txt",
        )
        repair_prompt = load_legacy_prompt(
            self.repair_prompt_path,
            "local_llm_json_repair_prompt.txt",
        )
        try:
            raw_payload = LocalLLMClient(self.settings).generate_json(
                text=text,
                system_prompt=prompt,
                repair_prompt=repair_prompt,
            )
        except Exception as exc:
            raise LocalLlmExtractionError(str(exc)) from exc
        payload = normalize_extraction_payload(raw_payload)
        return extractor_output_from_payload(payload, method=self.method)

    def _extract_via_remote_worker(self, text: str) -> ExtractorOutput:
        from court_ocr_extract.remote_worker.client import RemoteWorkerClient

        payload = RemoteWorkerClient.from_settings(self.settings).extract(text)
        if "method" in payload and "case_fields" in payload:
            return ExtractorOutput(**payload)
        return extractor_output_from_payload(
            normalize_extraction_payload(payload),
            method="remote_local_llm",
        )


class MockLocalLLMExtractor:
    """Synthetic typed extractor; never use it to judge real extraction quality."""

    method = "mock_local_llm"

    def extract(self, text: str) -> ExtractorOutput:
        output = anchor_support_output(text)
        output.method = self.method
        output.warnings.append("Mock local LLM extractor used; synthetic tests only.")
        for field in output.case_fields.values():
            field.source_method = self.method
            field.reasoning_brief = (
                field.reasoning_brief or "Mock extracted from synthetic text."
            )
            field.reason = field.reasoning_brief
        for participant in output.participants:
            for field in participant.values():
                field.source_method = self.method
                field.reasoning_brief = (
                    field.reasoning_brief or "Mock extracted from synthetic text."
                )
                field.reason = field.reasoning_brief
        return output


def extractor_output_from_payload(
    payload: dict[str, Any],
    method: str,
) -> ExtractorOutput:
    case_fields: dict[str, FieldValue] = {}
    raw_case = payload.get("case_info") or {}
    for key in CASE_FIELD_KEYS:
        case_fields[key] = _field_from_payload(raw_case.get(key), method=method)

    participants = []
    for raw_participant in payload.get("participants") or []:
        participants.append(
            {
                key: _field_from_payload(raw_participant.get(key), method=method)
                for key in PARTICIPANT_FIELD_KEYS
            }
        )

    warnings = [str(item) for item in payload.get("warnings") or []]
    if payload.get("reasoning_summary"):
        warnings.append(f"Model reasoning: {payload['reasoning_summary']}")
    return ExtractorOutput(
        method=method,
        case_fields=case_fields,
        participants=participants,
        warnings=warnings,
    )


def _field_from_payload(value: Any, method: str) -> FieldValue:
    if not isinstance(value, dict):
        return FieldValue(
            value=None,
            confidence=0.0,
            evidence_text=None,
            reasoning_brief="Missing field object in local LLM JSON.",
            source_method=method,
        )
    return FieldValue(
        value=value.get("value"),
        confidence=_safe_confidence(value.get("confidence")),
        evidence_text=value.get("evidence_text"),
        reasoning_brief=value.get("reasoning_brief"),
        source_method=method,
    )


def _safe_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def _post_json(url: str, payload: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_prompt() -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / "extraction_prompt.vi.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Return only strict JSON following the extraction schema."
