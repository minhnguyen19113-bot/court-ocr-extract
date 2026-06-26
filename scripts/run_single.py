from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.models import model_to_dict
from court_ocr_extract.pipeline import process_pdf, process_text_file
from court_ocr_extract.privacy import redact_sensitive_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Xử lý một PDF hoặc một file text OCR có sẵn.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf", type=Path, help="Đường dẫn PDF scan.")
    source.add_argument("--text", type=Path, help="Đường dẫn file text OCR synthetic hoặc OCR có sẵn.")
    parser.add_argument("--dpi", type=int, default=None, help="DPI render PDF.")
    parser.add_argument("--max-pages-before-marker", "--max-scan-pages", "--max-pages", type=int, default=None)
    parser.add_argument("--mode", choices=["local-only", "remote-gpu-worker"], default=None)
    parser.add_argument("--stop-on-marker", "--stop-after-marker", action="store_true")
    parser.add_argument("--no-stop-on-marker", action="store_true")
    parser.add_argument("--remove-red-stamp", action="store_true")
    parser.add_argument("--use-local-llm", action="store_true")
    parser.add_argument("--no-local-llm", action="store_true")
    parser.add_argument("--mock-ocr", action="store_true")
    parser.add_argument("--mock-local-llm", action="store_true")
    parser.add_argument("--force", action="store_true", help="Bỏ cache OCR và xử lý lại.")
    args = parser.parse_args()

    if args.max_pages_before_marker is not None and args.max_pages_before_marker < 1:
        parser.error("--max-pages-before-marker must be >= 1.")

    settings = get_settings()
    if args.mode:
        settings.processing_mode = args.mode
        settings.use_remote_gpu_worker = args.mode == "remote-gpu-worker"
    if args.mock_ocr:
        settings.enable_mock_ocr = True
    if args.mock_local_llm:
        settings.enable_mock_local_llm = True
    stop_on_marker = False if args.no_stop_on_marker else (args.stop_on_marker or settings.stop_on_section_marker)
    use_local_llm = False if args.no_local_llm else (args.use_local_llm or settings.enable_local_llm)

    if args.pdf:
        result = process_pdf(
            args.pdf,
            dpi=args.dpi,
            max_scan_pages=args.max_pages_before_marker,
            stop_on_marker=stop_on_marker,
            remove_red_stamp=args.remove_red_stamp,
            use_local_llm=use_local_llm,
            force=args.force,
            settings=settings,
        )
    else:
        result = process_text_file(args.text, settings=settings, use_local_llm=use_local_llm)

    print(
        json.dumps(
            redact_sensitive_payload(
                model_to_dict(result),
                include_sensitive=settings.persist_sensitive_json_text or settings.debug_sensitive,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
