from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from court_ocr_extract.local_llm.client import classify_llm_error


UrlOpen = Callable[..., Any]


def check_llm_backend(settings: Any, *, urlopen: UrlOpen | None = None) -> dict[str, Any]:
    opener = urlopen or urllib.request.urlopen
    base_url = str(getattr(settings, "local_llm_base_url", "")).rstrip("/")
    model = str(
        getattr(settings, "local_llm_model_name", "")
        or getattr(settings, "local_llm_model", "")
    )
    provider = str(getattr(settings, "local_llm_provider", "vllm"))
    timeout = float(getattr(settings, "local_llm_timeout_seconds", 30.0))
    result = {
        "ok": False,
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "models_endpoint_ok": False,
        "model_available": False,
        "chat_completion_ok": False,
        "error_type": None,
        "error": None,
    }
    if not base_url or not model:
        result.update(
            error_type="llm_configuration_invalid",
            error="LOCAL_LLM_BASE_URL and LOCAL_LLM_MODEL_NAME are required.",
        )
        return result

    try:
        models = _request_json(
            urllib.request.Request(base_url + "/models", method="GET"),
            timeout=timeout,
            urlopen=opener,
        )
        result["models_endpoint_ok"] = True
        available = {
            str(item.get("id"))
            for item in models.get("data", [])
            if isinstance(item, dict) and item.get("id")
        }
        result["model_available"] = model in available
        if not result["model_available"]:
            raise RuntimeError(f"Configured model is not listed by /models: {model}")

        body = {
            "model": model,
            "temperature": 0,
            "max_tokens": 8,
            "messages": [
                {"role": "user", "content": "Trả về JSON: {\"ok\": true}"}
            ],
        }
        chat = _request_json(
            urllib.request.Request(
                base_url + "/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout=timeout,
            urlopen=opener,
        )
        choices = chat.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Chat completion response has no choices.")
        result["chat_completion_ok"] = True
        result["ok"] = True
    except Exception as exc:
        result["error_type"] = classify_llm_error(exc)
        result["error"] = str(exc)
    return result


def _request_json(request: urllib.request.Request, *, timeout: float, urlopen: UrlOpen) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Local LLM HTTP {exc.code}: {detail[:500]}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ConnectionError("Không kết nối được local LLM endpoint.") from exc
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("Local LLM endpoint returned a non-object JSON payload.")
    return payload
