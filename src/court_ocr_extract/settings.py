from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STOP_MARKER = "NỘI DUNG VỤ ÁN"


@dataclass(frozen=True)
class PipelineSettings:
    project_root: Path = PROJECT_ROOT
    stop_marker: str = DEFAULT_STOP_MARKER
    max_pages_before_marker: int = 7
    ocr_dpi: int = 300
    save_debug_visual: bool = False
    save_debug_json: bool = False

    # Canonical OCR default for the rebuild. Tesseract settings are legacy optional.
    ocr_backend: str = "surya"
    fallback_ocr_backend: str = ""
    tesseract_cmd: str = ""
    tesseract_lang: str = "vie+eng"

    enable_cloud_ocr: bool = False
    google_application_credentials: str = ""
    google_cloud_project: str = ""
    google_location: str = "us"
    google_document_ai_processor_id: str = ""
    openai_api_key: str = ""
    openai_ocr_model: str = "gpt-4.1-mini"
    google_api_key: str = ""
    gemini_ocr_model: str = "gemini-2.5-flash"
    enable_surya_ocr: bool = True

    extractor_backend: str = "local_llm"
    enable_local_llm_extraction: bool = True
    local_llm_provider: str = "vllm"
    local_llm_model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    local_llm_base_url: str = "http://127.0.0.1:8001/v1"
    local_llm_temperature: float = 0.0
    local_llm_timeout_seconds: float = 300.0
    local_llm_json_mode: bool = True
    local_llm_max_tokens: int = 4096
    vlm_provider: str = "ollama"
    vlm_model_name: str = "qwen2.5vl:7b"
    vlm_base_url: str = "http://127.0.0.1:11434"
    vlm_temperature: float = 0.0
    vlm_timeout_seconds: float = 600.0
    vlm_render_dpi: int = 200
    vlm_max_pages: int = 0
    enable_cloud_extraction: bool = False
    openai_extraction_model: str = "gpt-4.1-mini"
    gemini_extraction_model: str = "gemini-2.5-flash"
    llama_cpp_binary: str = ""

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def output_dir(self) -> Path:
        return self.project_root / "outputs"

    @property
    def raw_upload_dir(self) -> Path:
        return self.data_dir / "raw_pdfs" / "uploads"

    @property
    def ocr_cache_dir(self) -> Path:
        return self.output_dir / "ocr_cache"

    @property
    def debug_visual_dir(self) -> Path:
        return self.output_dir / "debug_visual"

    @property
    def extraction_draft_dir(self) -> Path:
        return self.output_dir / "extraction_draft"

    @property
    def excel_dir(self) -> Path:
        return self.output_dir / "excel"

    def ensure_output_dirs(self) -> None:
        for path in [self.ocr_cache_dir, self.debug_visual_dir, self.excel_dir]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> PipelineSettings:
    _load_dotenv(PROJECT_ROOT / ".env")
    return PipelineSettings(
        stop_marker=_env("STOP_MARKER", _env("SECTION_MARKER", DEFAULT_STOP_MARKER)),
        max_pages_before_marker=_env_int("MAX_PAGES_BEFORE_CONTENT_MARKER", 7),
        ocr_dpi=_env_int("OCR_DPI", 300),
        save_debug_visual=_env_bool("SAVE_DEBUG_VISUAL", False),
        save_debug_json=_env_bool("SAVE_DEBUG_JSON", False),
        ocr_backend=_env("OCR_BACKEND", "surya"),
        fallback_ocr_backend=_env("FALLBACK_OCR_BACKEND", ""),
        tesseract_cmd=_env("TESSERACT_CMD", ""),
        tesseract_lang=_env("TESSERACT_LANG", "vie+eng"),
        enable_cloud_ocr=_env_bool("ENABLE_CLOUD_OCR", False),
        google_application_credentials=_env("GOOGLE_APPLICATION_CREDENTIALS", ""),
        google_cloud_project=_env("GOOGLE_CLOUD_PROJECT", ""),
        google_location=_env("GOOGLE_LOCATION", "us"),
        google_document_ai_processor_id=_env("GOOGLE_DOCUMENT_AI_PROCESSOR_ID", ""),
        openai_api_key=_env("OPENAI_API_KEY", ""),
        openai_ocr_model=_env("OPENAI_OCR_MODEL", "gpt-4.1-mini"),
        google_api_key=_env("GOOGLE_API_KEY", ""),
        gemini_ocr_model=_env("GEMINI_OCR_MODEL", "gemini-2.5-flash"),
        enable_surya_ocr=_env_bool("ENABLE_SURYA_OCR", True),
        extractor_backend=_env("EXTRACTOR_BACKEND", "local_llm"),
        enable_local_llm_extraction=_env_bool("ENABLE_LOCAL_LLM_EXTRACTION", True),
        local_llm_provider=_env("LOCAL_LLM_PROVIDER", "vllm"),
        local_llm_model_name=_env("LOCAL_LLM_MODEL_NAME", "Qwen/Qwen2.5-14B-Instruct"),
        local_llm_base_url=_env("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8001/v1"),
        local_llm_temperature=_env_float("LOCAL_LLM_TEMPERATURE", 0.0),
        local_llm_timeout_seconds=_env_float("LOCAL_LLM_TIMEOUT_SECONDS", 300.0),
        local_llm_json_mode=_env_bool("LOCAL_LLM_JSON_MODE", True),
        local_llm_max_tokens=_env_int("LOCAL_LLM_MAX_TOKENS", 4096),
        vlm_provider=_env("VLM_PROVIDER", "ollama"),
        vlm_model_name=_env("VLM_MODEL_NAME", "qwen2.5vl:7b"),
        vlm_base_url=_env("VLM_BASE_URL", "http://127.0.0.1:11434"),
        vlm_temperature=_env_float("VLM_TEMPERATURE", 0.0),
        vlm_timeout_seconds=_env_float("VLM_TIMEOUT_SECONDS", 600.0),
        vlm_render_dpi=_env_int("VLM_RENDER_DPI", 200),
        vlm_max_pages=_env_int("VLM_MAX_PAGES", 0),
        enable_cloud_extraction=_env_bool("ENABLE_CLOUD_EXTRACTION", False),
        openai_extraction_model=_env("OPENAI_EXTRACTION_MODEL", "gpt-4.1-mini"),
        gemini_extraction_model=_env("GEMINI_EXTRACTION_MODEL", "gemini-2.5-flash"),
        llama_cpp_binary=_env("LLAMA_CPP_BINARY", ""),
    )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default
