from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from court_ocr_extract.extractors.base import ExtractorBackendStatus, normalize_extraction, parse_json_object
from court_ocr_extract.settings import PipelineSettings


class OpenAIExtractor:
    name = "openai"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> ExtractorBackendStatus:
        if not self.settings.enable_cloud_extraction:
            return ExtractorBackendStatus(self.name, False, "ENABLE_CLOUD_EXTRACTION must be true for OpenAI.")
        if not self.settings.openai_api_key:
            return ExtractorBackendStatus(self.name, False, "OPENAI_API_KEY is required.")
        return ExtractorBackendStatus(self.name, True, "OpenAI extraction configuration is present.")

    def extract_from_text(self, text: str, *, case_id: str) -> dict[str, Any]:
        status = self.check_available()
        if not status.available:
            raise RuntimeError(status.reason)
        payload = {
            "model": self.settings.openai_extraction_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": _load_prompt() + "\n\nOCR TEXT:\n" + text},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.openai_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return normalize_extraction(parse_json_object(content))


def _load_prompt() -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / "extraction_prompt.vi.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Return strict extraction JSON."
