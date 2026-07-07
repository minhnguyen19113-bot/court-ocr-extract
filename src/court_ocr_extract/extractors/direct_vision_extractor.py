from __future__ import annotations

import base64
import json
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from court_ocr_extract.extractors.base import ExtractorBackendStatus, normalize_extraction, parse_json_object
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.settings import PipelineSettings


class DirectVisionExtractor:
    def __init__(self, settings: PipelineSettings, name: str) -> None:
        self.settings = settings
        self.name = name

    def check_available(self) -> ExtractorBackendStatus:
        if not self.settings.enable_cloud_extraction:
            return ExtractorBackendStatus(self.name, False, "ENABLE_CLOUD_EXTRACTION must be true for direct vision.")
        if self.name.endswith("openai") and not self.settings.openai_api_key:
            return ExtractorBackendStatus(self.name, False, "OPENAI_API_KEY is required.")
        if self.name.endswith("gemini") and not self.settings.google_api_key:
            return ExtractorBackendStatus(self.name, False, "GOOGLE_API_KEY is required.")
        return ExtractorBackendStatus(self.name, True, "Direct vision configuration is present.")

    def extract_from_text(self, text: str, *, case_id: str) -> dict[str, Any]:
        raise RuntimeError("Direct vision extraction requires PDF/image input, not OCR text.")

    def extract_from_pdf(self, pdf_path: Path, *, case_id: str, max_pages: int) -> dict[str, Any]:
        status = self.check_available()
        if not status.available:
            raise RuntimeError(status.reason)
        with tempfile.TemporaryDirectory(prefix="court_direct_vision_") as temp_dir:
            images = render_pdf_pages(pdf_path, Path(temp_dir) / "pages", dpi=self.settings.ocr_dpi, max_pages=max_pages)
            if self.name.endswith("openai"):
                raw = self._openai_extract([page.image_path for page in images])
            else:
                raw = self._gemini_extract([page.image_path for page in images])
        return normalize_extraction(parse_json_object(raw))

    def _openai_extract(self, image_paths: list[Path]) -> str:
        content: list[dict[str, Any]] = [{"type": "text", "text": _load_prompt()}]
        for image_path in image_paths:
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}})
        payload = {
            "model": self.settings.openai_extraction_model,
            "temperature": 0,
            "messages": [{"role": "user", "content": content}],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.openai_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["choices"][0]["message"]["content"])

    def _gemini_extract(self, image_paths: list[Path]) -> str:
        model = urllib.parse.quote(self.settings.gemini_extraction_model, safe="")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.settings.google_api_key}"
        parts: list[dict[str, Any]] = [{"text": _load_prompt()}]
        for image_path in image_paths:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(image_path.read_bytes()).decode("ascii"),
                    }
                }
            )
        payload = {"generationConfig": {"temperature": 0, "responseMimeType": "application/json"}, "contents": [{"role": "user", "parts": parts}]}
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["candidates"][0]["content"]["parts"][0]["text"])


def _load_prompt() -> str:
    path = Path(__file__).resolve().parents[3] / "prompts" / "direct_vision_extraction_prompt.vi.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Extract Vietnamese court fields and return strict JSON."
