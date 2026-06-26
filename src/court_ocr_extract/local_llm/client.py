from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from court_ocr_extract.local_llm.json_parser import StrictJsonError, parse_json_object


class LocalLLMClientError(RuntimeError):
    pass


class LocalLLMClient:
    def __init__(self, settings) -> None:
        self.settings = settings

    def generate_json(
        self,
        *,
        text: str,
        system_prompt: str,
        repair_prompt: str | None = None,
    ) -> dict[str, Any]:
        content = self._call_chat(system_prompt=system_prompt, user_content=text)
        try:
            return parse_json_object(content)
        except StrictJsonError:
            if not repair_prompt:
                raise
            repaired = self._call_chat(
                system_prompt=repair_prompt,
                user_content=(
                    "JSON lỗi cần sửa, chỉ trả JSON object hợp lệ:\n"
                    f"{content}\n\n"
                    "Không thêm markdown, không thêm giải thích."
                ),
            )
            return parse_json_object(repaired)

    def _call_chat(self, *, system_prompt: str, user_content: str) -> str:
        provider = self.settings.local_llm_provider
        if provider == "ollama":
            return self._call_ollama(system_prompt=system_prompt, user_content=user_content)
        if provider in {"vllm", "llama_cpp", "openai_compatible"}:
            return self._call_openai_compatible(system_prompt=system_prompt, user_content=user_content)
        if provider == "transformers":
            raise LocalLLMClientError(
                "Provider transformers chưa được chạy trực tiếp trong process này. "
                "Hãy dùng vLLM/llama.cpp/Ollama hoặc remote GPU worker để tránh khóa UI/API."
            )
        raise LocalLLMClientError(
            f"Unsupported LOCAL_LLM_PROVIDER={provider!r}. "
            "Dùng ollama, vllm, llama_cpp, transformers hoặc mock."
        )

    def _call_openai_compatible(self, *, system_prompt: str, user_content: str) -> str:
        body = {
            "model": self.settings.local_llm_model,
            "temperature": self.settings.local_llm_temperature,
            "max_tokens": self.settings.local_llm_max_new_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        payload = self._post_json(
            self.settings.local_llm_base_url.rstrip("/") + "/chat/completions",
            body,
            timeout=180,
        )
        try:
            return str(payload["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LocalLLMClientError("Local LLM response does not match chat/completions format.") from exc

    def _call_ollama(self, *, system_prompt: str, user_content: str) -> str:
        body = {
            "model": self.settings.local_llm_model,
            "stream": False,
            "format": "json",
            "options": {"temperature": self.settings.local_llm_temperature},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        payload = self._post_json(
            self.settings.local_llm_base_url.rstrip("/") + "/api/chat",
            body,
            timeout=180,
        )
        try:
            return str(payload["message"]["content"])
        except (KeyError, TypeError) as exc:
            raise LocalLLMClientError("Ollama response does not match /api/chat format.") from exc

    def _post_json(self, url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise LocalLLMClientError(
                "Không kết nối được local LLM. Hãy chạy model local/remote worker "
                "hoặc bật ENABLE_MOCK_LOCAL_LLM=true để test synthetic."
            ) from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LocalLLMClientError("Local LLM server returned non-JSON response.") from exc
        if not isinstance(payload, dict):
            raise LocalLLMClientError("Local LLM server response must be a JSON object.")
        return payload
