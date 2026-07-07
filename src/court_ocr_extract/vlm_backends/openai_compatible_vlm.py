from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from court_ocr_extract.vlm_backends.base import (
    VLMBackendStatus,
    VLMPageResult,
    count_unreadable_markers,
)


class OpenAICompatibleVLMBackend:
    provider = "openai_compatible"

    def __init__(
        self,
        *,
        model_name: str,
        base_url: str,
        timeout_seconds: float,
        temperature: float,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def check_available(self) -> VLMBackendStatus:
        if not self.model_name:
            return VLMBackendStatus(self.provider, False, "VLM_MODEL_NAME is required.")
        if not self.base_url:
            return VLMBackendStatus(self.provider, False, "VLM_BASE_URL is required.")
        return VLMBackendStatus(
            self.provider,
            True,
            "OpenAI-compatible VLM configuration is present; endpoint is not probed by default.",
        )

    def read_page(self, image_path: Path, prompt: str, page_number: int) -> VLMPageResult:
        started = time.perf_counter()
        encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        body = {
            "model": self.model_name,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt.format(page_number=page_number)},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded}"},
                        },
                    ],
                }
            ],
        }
        payload = self._post_json(_chat_url(self.base_url), body)
        text = str(payload["choices"][0]["message"]["content"])
        return VLMPageResult(
            page_index=page_number,
            text=text,
            warnings=[] if text.strip() else ["VLM returned empty text."],
            timing={"total_seconds": round(time.perf_counter() - started, 6)},
            raw_response=text,
            unreadable_count=count_unreadable_markers(text),
        )

    def _post_json(self, url: str, body: dict) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI-compatible VLM request failed: {exc}") from exc


def _chat_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"

