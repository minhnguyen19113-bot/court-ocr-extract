from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


WORKER_TEMP_DIR = Path(tempfile.gettempdir()) / "court_ocr_gpu_worker"


def ensure_worker_temp_dir() -> Path:
    WORKER_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return WORKER_TEMP_DIR


def cleanup_worker_temp() -> int:
    if not WORKER_TEMP_DIR.exists():
        return 0
    removed = sum(1 for item in WORKER_TEMP_DIR.rglob("*") if item.is_file())
    shutil.rmtree(WORKER_TEMP_DIR, ignore_errors=True)
    WORKER_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return removed
