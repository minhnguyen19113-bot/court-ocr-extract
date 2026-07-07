from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from court_ocr_extract.extractors.base import (
    ExtractorBackendStatus,
    normalize_extraction,
    parse_json_object,
)
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
