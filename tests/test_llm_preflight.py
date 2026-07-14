from __future__ import annotations

import json
import urllib.error

from court_ocr_extract.local_llm.preflight import check_llm_backend
from court_ocr_extract.settings import PipelineSettings


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_preflight_checks_models_and_chat_completion() -> None:
    calls = []

    def fake_open(request, timeout):
        calls.append((request.full_url, request.get_method()))
        if request.full_url.endswith("/models"):
            return _Response({"data": [{"id": "Qwen/Qwen2.5-3B-Instruct"}]})
        body = json.loads(request.data)
        assert body["max_tokens"] == 8
        return _Response({"choices": [{"message": {"content": '{"ok":true}'}}]})

    result = check_llm_backend(PipelineSettings(), urlopen=fake_open)

    assert result["ok"] is True
    assert result["models_endpoint_ok"] is True
    assert result["chat_completion_ok"] is True
    assert [method for _, method in calls] == ["GET", "POST"]
    assert "api_key" not in json.dumps(result).lower()


def test_preflight_connection_refused_is_reported() -> None:
    def refused(request, timeout):
        raise urllib.error.URLError("connection refused")

    result = check_llm_backend(PipelineSettings(), urlopen=refused)

    assert result["ok"] is False
    assert result["error_type"] == "llm_connection_failed"
