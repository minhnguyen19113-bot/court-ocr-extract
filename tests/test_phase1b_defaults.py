from __future__ import annotations

from court_ocr_extract.ocr_backends import get_ocr_backend
from court_ocr_extract.settings import PipelineSettings


def test_phase1b_pipeline_settings_default_to_surya() -> None:
    settings = PipelineSettings()

    assert settings.ocr_backend == "surya"
    assert settings.enable_surya_ocr is True
    assert settings.local_llm_provider == "vllm"
    assert settings.local_llm_model_name == "Qwen/Qwen2.5-14B-Instruct"


def test_surya_backend_alias_is_supported_without_runtime_import() -> None:
    backend = get_ocr_backend("surya", PipelineSettings())

    assert backend.name == "surya"
