from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    def __init__(self) -> None:
        _load_dotenv(PROJECT_ROOT / ".env")

        self.app_env = os.getenv("APP_ENV", "local")
        self.stop_on_section_marker = _env_bool("STOP_ON_SECTION_MARKER", True)
        self.section_marker = _repair_mojibake(os.getenv("SECTION_MARKER", "NỘI DUNG VỤ ÁN"))
        self.max_scan_pages = _env_int(
            "MAX_PAGES_BEFORE_CONTENT_MARKER",
            _env_int("MAX_SCAN_PAGES", _env_int("MAX_PAGES_UNTIL_MARKER", 7)),
        )
        self.ocr_dpi = _env_int("OCR_DPI", _env_int("DEFAULT_DPI", 300))
        self.ocr_dpi_for_blurry_scan = _env_int(
            "OCR_DPI_FOR_BLURRY_SCAN",
            _env_int("HIGH_DPI", 400),
        )
        self.extract_without_marker = _env_bool("EXTRACT_WITHOUT_MARKER", True)
        self.force_full_ocr = _env_bool("FORCE_FULL_OCR", False)
        self.force_reprocess = _env_bool("FORCE_REPROCESS", False)
        self.enable_red_stamp_removal = _env_bool("ENABLE_RED_STAMP_REMOVAL", False)
        self.enable_cloud_llm = _env_bool(
            "ENABLE_CLOUD_LLM_EXTRACTION",
            _env_bool("ENABLE_CLOUD_LLM", False),
        )
        self.enable_local_llm = _env_bool(
            "ENABLE_LOCAL_LLM_EXTRACTION",
            _env_bool("ENABLE_LOCAL_LLM", False),
        )
        self.enable_gliner = _env_bool("ENABLE_GLINER", False)
        self.enable_local_llm_correction = _env_bool("ENABLE_LOCAL_LLM_CORRECTION", False)
        self.enable_mock_ocr = _env_bool("ENABLE_MOCK_OCR", False)
        self.enable_mock_local_llm = _env_bool("ENABLE_MOCK_LOCAL_LLM", False)
        self.enable_mock_gliner = _env_bool("ENABLE_MOCK_GLINER", False)
        self.debug_keep_images = _env_bool("DEBUG_KEEP_IMAGES", False)
        self.debug_sensitive = _env_bool("DEBUG_SENSITIVE", False)
        self.log_full_text = _env_bool("LOG_FULL_TEXT", False)
        self.persist_ocr_text_artifacts = _env_bool("PERSIST_OCR_TEXT_ARTIFACTS", False)
        self.persist_sensitive_json_text = _env_bool("PERSIST_SENSITIVE_TEXT_IN_JSON", False)

        self.local_llm_provider = os.getenv(
            "LOCAL_LLM_PROVIDER",
            os.getenv("LOCAL_LLM_BACKEND", "vllm"),
        )
        self.local_llm_backend = self.local_llm_provider
        self.local_llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8001/v1")
        self.local_llm_model = os.getenv(
            "LOCAL_LLM_MODEL_NAME",
            os.getenv("LOCAL_LLM_MODEL", "Qwen/Qwen3-4B-Instruct"),
        )
        self.local_llm_quantization = os.getenv("LOCAL_LLM_QUANTIZATION", "AWQ")
        self.local_llm_max_new_tokens = _env_int(
            "LOCAL_LLM_MAX_TOKENS",
            _env_int("LOCAL_LLM_MAX_NEW_TOKENS", 2048),
        )
        self.local_llm_temperature = _env_float("LOCAL_LLM_TEMPERATURE", 0.0)
        self.gliner_model = os.getenv("GLINER_MODEL", "urchade/gliner_multi-v2.1")
        self.surya_langs = os.getenv("SURYA_LANGS", "vi")

        self.processing_mode = os.getenv("PROCESSING_MODE", "local-only")
        self.use_remote_gpu_worker = _env_bool("USE_REMOTE_GPU_WORKER", False) or (
            self.processing_mode == "remote-gpu-worker"
        )
        self.gpu_worker_base_url = os.getenv("GPU_WORKER_BASE_URL", "")
        self.gpu_worker_token = os.getenv("GPU_WORKER_TOKEN", "")
        self.gpu_worker_timeout_seconds = _env_float("GPU_WORKER_TIMEOUT_SECONDS", 180.0)
        self.gpu_worker_retries = _env_int("GPU_WORKER_RETRIES", 2)
        self.gpu_worker_fallback = _env_bool("GPU_WORKER_FALLBACK", True)
        self.gpu_worker_fallback_to_mock = _env_bool("GPU_WORKER_FALLBACK_TO_MOCK", False)

        self.data_dir = PROJECT_ROOT / "data"
        self.outputs_dir = PROJECT_ROOT / "outputs"
        self.raw_pdf_dir = self.data_dir / "raw_pdfs"
        self.private_pdf_dir = self.data_dir / "private_pdfs"
        self.images_dir = self.data_dir / "images"
        self.processed_intermediate_dir = self.data_dir / "processed" / "intermediate"
        self.processed_images_dir = self.data_dir / "processed_images"
        self.ocr_raw_dir = self.data_dir / "ocr_raw"
        self.ocr_corrected_dir = self.data_dir / "ocr_corrected"
        self.annotations_dir = self.data_dir / "annotations"
        self.excel_dir = self.outputs_dir / "excel"
        self.json_dir = self.outputs_dir / "json"
        self.bbox_debug_dir = self.outputs_dir / "bbox_debug"
        self.logs_dir = self.outputs_dir / "logs"
        self.workflow_dir = self.outputs_dir / "workflow"
        self.checkpoint_dir = self.outputs_dir / "checkpoints"
        self.cache_dir = self.outputs_dir / "cache"

        # Backward-compatible aliases used by earlier scripts.
        self.default_dpi = self.ocr_dpi
        self.high_dpi = self.ocr_dpi_for_blurry_scan
        self.max_pages_until_marker = self.max_scan_pages
        self.enable_llm_correction = self.enable_local_llm_correction
        self.enable_llm_extraction = self.enable_local_llm
        self.llm_provider = "local" if self.enable_local_llm else ""
        self.llm_model = self.local_llm_model

    @property
    def surya_language_list(self) -> list[str]:
        return [item.strip() for item in self.surya_langs.split(",") if item.strip()]

    def ensure_dirs(self) -> None:
        for directory in [
            self.raw_pdf_dir,
            self.private_pdf_dir,
            self.images_dir,
            self.processed_intermediate_dir,
            self.processed_images_dir,
            self.ocr_raw_dir,
            self.ocr_corrected_dir,
            self.annotations_dir,
            self.excel_dir,
            self.json_dir,
            self.bbox_debug_dir,
            self.logs_dir,
            self.workflow_dir,
            self.checkpoint_dir,
            self.cache_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _repair_mojibake(value: str) -> str:
    """Repair common UTF-8-as-CP1252 mojibake in existing local config values."""
    if "Ã" not in value and "áº" not in value and "á»" not in value:
        return value
    try:
        return value.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return value
