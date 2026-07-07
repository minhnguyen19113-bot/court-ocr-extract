from __future__ import annotations

from typing import Any

from court_ocr_extract.vlm_backends.base import VLMBackend, VLMBackendStatus, VLMPageResult
from court_ocr_extract.vlm_backends.fake_vlm import FakeVLMBackend
from court_ocr_extract.vlm_backends.ollama_vlm import OllamaVLMBackend
from court_ocr_extract.vlm_backends.openai_compatible_vlm import OpenAICompatibleVLMBackend


def get_vlm_backend(settings: Any, provider: str | None = None) -> VLMBackend:
    provider_name = (provider or settings.vlm_provider).strip().lower()
    if provider_name == "fake":
        return FakeVLMBackend()
    if provider_name == "ollama":
        return OllamaVLMBackend(
            model_name=settings.vlm_model_name,
            base_url=settings.vlm_base_url,
            timeout_seconds=settings.vlm_timeout_seconds,
            temperature=settings.vlm_temperature,
        )
    if provider_name in {"openai_compatible", "vllm", "llama_cpp"}:
        return OpenAICompatibleVLMBackend(
            model_name=settings.vlm_model_name,
            base_url=settings.vlm_base_url,
            timeout_seconds=settings.vlm_timeout_seconds,
            temperature=settings.vlm_temperature,
        )
    raise ValueError(f"Unknown VLM provider: {provider_name}")


__all__ = [
    "FakeVLMBackend",
    "OllamaVLMBackend",
    "OpenAICompatibleVLMBackend",
    "VLMBackend",
    "VLMBackendStatus",
    "VLMPageResult",
    "get_vlm_backend",
]

