from __future__ import annotations

from court_ocr_extract.extractors.base import ExtractorBackend
from court_ocr_extract.settings import PipelineSettings, get_settings


def get_extractor_backend(name: str | None = None, settings: PipelineSettings | None = None) -> ExtractorBackend:
    settings = settings or get_settings()
    backend_name = (name or settings.extractor_backend).strip().lower()
    if backend_name == "local_llm":
        from court_ocr_extract.extractors.local_llm_extractor import LocalLLMExtractor

        return LocalLLMExtractor(settings)
    if backend_name == "openai":
        from court_ocr_extract.extractors.openai_extractor import OpenAIExtractor

        return OpenAIExtractor(settings)
    if backend_name == "gemini":
        from court_ocr_extract.extractors.gemini_extractor import GeminiExtractor

        return GeminiExtractor(settings)
    if backend_name in {"direct_vision_openai", "direct_vision_gemini"}:
        from court_ocr_extract.extractors.direct_vision_extractor import DirectVisionExtractor

        return DirectVisionExtractor(settings, backend_name)
    if backend_name == "rule_support_only_for_validation":
        from court_ocr_extract.extractors.rule_support import RuleSupportExtractor

        return RuleSupportExtractor()
    raise ValueError(f"Unknown extractor backend: {backend_name}")


__all__ = ["ExtractorBackend", "get_extractor_backend"]
