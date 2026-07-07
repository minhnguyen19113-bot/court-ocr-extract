from __future__ import annotations

import argparse
import os
import platform
import sys
import urllib.request
from pathlib import Path

from court_ocr_extract.extractors import get_extractor_backend
from court_ocr_extract.ocr_backends import get_ocr_backend
from court_ocr_extract.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr-backend", required=True)
    parser.add_argument("--extractor", required=True)
    args = parser.parse_args()

    settings = get_settings()
    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.platform()}")
    print(f"Output writable: {_check_writable(settings.output_dir)}")
    print(f"NVIDIA GPU visible: {_has_nvidia_gpu()}")

    ocr_status = get_ocr_backend(args.ocr_backend, settings).check_available()
    extractor_status = get_extractor_backend(args.extractor, settings).check_available()
    print(f"OCR backend {ocr_status.name}: {ocr_status.available} ({ocr_status.reason})")
    print(f"Extractor {extractor_status.name}: {extractor_status.available} ({extractor_status.reason})")

    if args.extractor == "local_llm":
        print(f"Local LLM endpoint reachable: {_check_local_endpoint(settings.local_llm_base_url)}")

    if not ocr_status.available or not extractor_status.available:
        raise SystemExit(1)


def _check_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".runtime_check.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _has_nvidia_gpu() -> bool:
    return bool(os.getenv("CUDA_VISIBLE_DEVICES")) or Path(r"C:\Program Files\NVIDIA Corporation").exists()


def _check_local_endpoint(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/", timeout=2) as response:
            return response.status < 500
    except Exception:
        return False


if __name__ == "__main__":
    main()
