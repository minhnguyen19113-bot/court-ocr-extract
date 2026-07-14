from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from court_ocr_extract.local_llm.budget import LocalLLMBudget, LocalLLMBudgetError
from court_ocr_extract.local_llm.json_parser import StrictJsonError, parse_json_object


class LocalLLMClientError(RuntimeError):
    def __init__(self, message: str, *, error_type: str = "llm_request_failed") -> None:
        super().__init__(message)
        self.error_type = error_type


class LocalLLMClient:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.budget = LocalLLMBudget.from_settings(settings)
        self.request_statuses: list[dict[str, Any]] = []

    def generate_json(
        self,
        *,
        text: str,
        system_prompt: str,
        repair_prompt: str | None = None,
        chunk_name: str = "request",
        chunked: bool = False,
    ) -> dict[str, Any]:
        content = self._call_chat(
            system_prompt=system_prompt,
            user_content=text,
            chunk_name=chunk_name,
            chunked=chunked,
        )
        try:
            return parse_json_object(content)
        except StrictJsonError:
            if not repair_prompt:
                raise
            repaired = self._call_chat(
                system_prompt=repair_prompt,
                user_content=(
                    "JSON lỗi cần sửa, chỉ trả JSON object hợp lệ:\n"
                    f"{content}\n\nKhông thêm markdown, không thêm giải thích."
                ),
                chunk_name=f"{chunk_name}:json_repair",
                chunked=chunked,
            )
            return parse_json_object(repaired)

    def _call_chat(
        self,
        *,
        system_prompt: str,
        user_content: str,
        chunk_name: str,
        chunked: bool,
    ) -> str:
        started = time.perf_counter()
        status = self._base_status(chunk_name=chunk_name, chunked=chunked)
        try:
            prepared, budget_meta = self.budget.prepare(
                system_prompt=system_prompt,
                user_content=user_content,
                chunked=chunked,
            )
            status.update(budget_meta)
            status["llm_actually_called"] = True
            provider = _provider(self.settings)
            if provider == "ollama":
                content = self._call_ollama(system_prompt=system_prompt, user_content=prepared)
            elif provider in {"vllm", "llama_cpp", "openai_compatible"}:
                content = self._call_openai_compatible(
                    system_prompt=system_prompt,
                    user_content=prepared,
                )
            elif provider == "transformers":
                raise LocalLLMClientError(
                    "Provider transformers chưa được chạy trực tiếp trong process này.",
                    error_type="llm_provider_unsupported",
                )
            else:
                raise LocalLLMClientError(
                    f"Unsupported LOCAL_LLM_PROVIDER={provider!r}.",
                    error_type="llm_provider_unsupported",
                )
            status.update({"request_ok": True, "response_ok": True})
            return content
        except LocalLLMBudgetError as exc:
            status.update(
                {
                    "budget_ok": False,
                    "error_type": exc.error_type,
                    "error_message": str(exc),
                }
            )
            raise LocalLLMClientError(str(exc), error_type=exc.error_type) from exc
        except Exception as exc:
            error_type = classify_llm_error(exc)
            status.update({"error_type": error_type, "error_message": str(exc)})
            if isinstance(exc, LocalLLMClientError):
                raise
            raise LocalLLMClientError(str(exc), error_type=error_type) from exc
        finally:
            status["duration_ms"] = round((time.perf_counter() - started) * 1000, 3)
            self.request_statuses.append(status)

    def _call_openai_compatible(self, *, system_prompt: str, user_content: str) -> str:
        body = {
            "model": _model(self.settings),
            "temperature": float(getattr(self.settings, "local_llm_temperature", 0.0)),
            "max_tokens": self.budget.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        payload = self._post_json(
            _base_url(self.settings) + "/chat/completions",
            body,
            timeout=_timeout(self.settings),
        )
        try:
            return str(payload["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LocalLLMClientError(
                "Local LLM response does not match chat/completions format.",
                error_type="llm_response_invalid",
            ) from exc

    def _call_ollama(self, *, system_prompt: str, user_content: str) -> str:
        body = {
            "model": _model(self.settings),
            "stream": False,
            "format": "json",
            "options": {
                "temperature": float(getattr(self.settings, "local_llm_temperature", 0.0)),
                "num_predict": self.budget.max_output_tokens,
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        payload = self._post_json(
            _base_url(self.settings) + "/api/chat",
            body,
            timeout=_timeout(self.settings),
        )
        try:
            return str(payload["message"]["content"])
        except (KeyError, TypeError) as exc:
            raise LocalLLMClientError(
                "Ollama response does not match /api/chat format.",
                error_type="llm_response_invalid",
            ) from exc

    def _post_json(self, url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            error_type = classify_llm_error(detail)
            raise LocalLLMClientError(
                f"Local LLM HTTP {exc.code}: {detail[:500]}",
                error_type=error_type,
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LocalLLMClientError(
                "Không kết nối được local LLM endpoint.",
                error_type="llm_connection_failed",
            ) from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LocalLLMClientError(
                "Local LLM server returned non-JSON response.",
                error_type="llm_response_invalid",
            ) from exc
        if not isinstance(payload, dict):
            raise LocalLLMClientError(
                "Local LLM server response must be a JSON object.",
                error_type="llm_response_invalid",
            )
        return payload

    def _base_status(self, *, chunk_name: str, chunked: bool) -> dict[str, Any]:
        return {
            "strategy": "",
            "chunk_name": chunk_name,
            "llm_required": False,
            "llm_available": True,
            "llm_actually_called": False,
            "provider": _provider(self.settings),
            "model": _model(self.settings),
            "base_url": _base_url(self.settings),
            "context_window": self.budget.context_window,
            "input_chars": 0,
            "estimated_input_tokens": 0,
            "max_output_tokens": self.budget.max_output_tokens,
            "budget_ok": False,
            "truncated": False,
            "chunked": chunked,
            "request_ok": False,
            "response_ok": False,
            "error_type": None,
            "error_message": None,
            "duration_ms": 0.0,
        }


def classify_llm_error(error: object) -> str:
    if isinstance(error, LocalLLMClientError):
        return error.error_type
    text = str(error).lower()
    if "maximum context length" in text or "context length" in text or "at least 8193" in text:
        return "llm_context_length_exceeded"
    if "context budget" in text:
        return "llm_context_budget_exceeded"
    if "connection" in text or "refused" in text or "timed out" in text or "kết nối" in text:
        return "llm_connection_failed"
    return "llm_request_failed"


def _provider(settings: Any) -> str:
    return str(getattr(settings, "local_llm_provider", "vllm")).lower()


def _model(settings: Any) -> str:
    return str(
        getattr(settings, "local_llm_model_name", "")
        or getattr(settings, "local_llm_model", "")
    )


def _base_url(settings: Any) -> str:
    return str(getattr(settings, "local_llm_base_url", "")).rstrip("/")


def _timeout(settings: Any) -> float:
    return float(getattr(settings, "local_llm_timeout_seconds", 180.0))
