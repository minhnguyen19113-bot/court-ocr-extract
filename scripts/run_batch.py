from __future__ import annotations

import argparse
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
from court_ocr_extract.pipeline import process_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Xử lý batch PDF theo queue có checkpoint/cache.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None, help="File Excel tổng hợp.")
    parser.add_argument("--output-excel", type=Path, default=None, help="Alias cho --output.")
    parser.add_argument("--mode", choices=["debug", "sample", "batch"], default="batch")
    parser.add_argument("--processing-mode", choices=["local-only", "remote-gpu-worker"], default=None)
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N PDFs after sorting.")
    parser.add_argument("--max-pages-before-marker", "--max-scan-pages", type=int, default=None)
    parser.add_argument("--dpi", type=int, default=None)
    parser.add_argument("--stop-on-marker", action="store_true")
    parser.add_argument("--remove-red-stamp", action="store_true")
    parser.add_argument("--use-local-llm", action="store_true")
    parser.add_argument("--no-local-llm", action="store_true")
    parser.add_argument("--mock-ocr", action="store_true")
    parser.add_argument("--mock-local-llm", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be >= 1.")

    settings = get_settings()
    if args.processing_mode:
        settings.processing_mode = args.processing_mode
        settings.use_remote_gpu_worker = args.processing_mode == "remote-gpu-worker"
    if args.mock_ocr:
        settings.enable_mock_ocr = True
    if args.mock_local_llm:
        settings.enable_mock_local_llm = True

    debug_limit = 3 if args.mode == "debug" else None
    sample_size = args.sample_size if args.mode == "sample" else None
    use_local_llm = False if args.no_local_llm else (args.use_local_llm or settings.enable_local_llm)

    summary = process_batch(
        args.input_dir,
        output_excel=args.output_excel or args.output,
        sample_size=sample_size,
        limit=args.limit,
        debug_limit=debug_limit,
        force=args.force,
        settings=settings,
        dpi=args.dpi,
        max_scan_pages=args.max_pages_before_marker,
        stop_on_marker=args.stop_on_marker or settings.stop_on_section_marker,
        remove_red_stamp=args.remove_red_stamp,
        use_local_llm=use_local_llm,
    )
    _print_safe_summary(summary)


def _print_safe_summary(summary: dict) -> None:
    print("")
    print("Batch finished.")
    print(f"  total: {summary.get('total', 0)}")
    print(f"  success: {summary.get('success', 0)}")
    print(f"  skipped: {summary.get('skipped', 0)}")
    print(f"  failed: {summary.get('failed', 0)}")
    print(f"  excel: {summary.get('combined_excel') or 'not_created'}")
    print(f"  summary_json: {summary.get('summary_json') or 'outputs/json/batch_summary.json'}")

    failures = summary.get("failures") or []
    if failures:
        print("  failures:")
        for item in failures[:10]:
            file_id = item.get("file_id", "unknown")
            error = " ".join(str(item.get("error", "")).split())
            if len(error) > 220:
                error = error[:217] + "..."
            print(f"    - file_id={file_id}: {error}")
        if len(failures) > 10:
            print(f"    - ... {len(failures) - 10} more failure(s), see summary_json")


if __name__ == "__main__":
    main()
