from __future__ import annotations

import io
import json
import urllib.error

import pytest

from court_ocr_extract.local_llm.client import LocalLLMClient, LocalLLMClientError
from court_ocr_extract.settings import PipelineSettings


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"choices":[{"message":{"content":"{\\"metadata\\":{}}"}}]}'


def test_long_prompt_is_trimmed_and_payload_has_positive_max_tokens(monkeypatch) -> None:
    bodies = []

    def fake_open(request, timeout):
        bodies.append(json.loads(request.data))
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    settings = PipelineSettings(
        local_llm_context_window=256,
        local_llm_max_output_tokens=64,
        local_llm_max_input_tokens=128,
        local_llm_max_input_chars=500,
        local_llm_safety_margin_tokens=32,
    )
    client = LocalLLMClient(settings)
    client.generate_json(text="x" * 2000, system_prompt="system", chunked=True)

    assert bodies[0]["max_tokens"] == 64
    assert len(bodies[0]["messages"][1]["content"]) < 2000
    status = client.request_statuses[0]
    assert status["truncated"] is True
    assert status["budget_ok"] is True
    assert status["estimated_input_tokens"] + 64 + 32 <= 256


def test_server_context_length_error_has_specific_error_type(monkeypatch) -> None:
    detail = b'{"error":"maximum context length is 8192 tokens"}'

    def context_error(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 400, "bad", {}, io.BytesIO(detail))

    monkeypatch.setattr("urllib.request.urlopen", context_error)
    client = LocalLLMClient(PipelineSettings())

    with pytest.raises(LocalLLMClientError) as raised:
        client.generate_json(text="small", system_prompt="system")

    assert raised.value.error_type == "llm_context_length_exceeded"
    assert client.request_statuses[0]["error_type"] == "llm_context_length_exceeded"

