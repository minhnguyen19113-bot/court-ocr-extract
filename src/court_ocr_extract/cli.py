from __future__ import annotations

import argparse
import inspect
import json
import os
import shutil
import webbrowser
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from court_ocr_extract.case_ids import case_files_for_paths, discover_pdfs
from court_ocr_extract.excel_writer import build_run_summary, write_excel
from court_ocr_extract.extractors import get_extractor_backend
from court_ocr_extract.extraction_pipeline import extract_from_ocr_cache_records, review_candidates_from_drafts
from court_ocr_extract.extraction_preview import write_extraction_preview
from court_ocr_extract.image_preprocess import make_before_after_compare, preprocess_image
from court_ocr_extract.image_processing.stamp_suppression import suppress_stamp_for_ocr
from court_ocr_extract.ocr_backends import get_ocr_backend
from court_ocr_extract.ocr_backends.surya_runtime import collect_surya_runtime_diagnostics
from court_ocr_extract.ocr_backends.base import OCRResult
from court_ocr_extract.ocr_cache import (
    OCRCacheRecord,
    read_ocr_cache_dir,
    safe_cache_metadata,
    write_ocr_cache_record,
)
from court_ocr_extract.pdf_render import parse_page_range, render_pdf_pages
from court_ocr_extract.pre_content_ab import run_pre_content_ab_test
from court_ocr_extract.progress import track
from court_ocr_extract.qa import print_safe_qa, qa_excel
from court_ocr_extract.red_seal import remove_red_seal_debug
from court_ocr_extract.review_html import (
    write_image_grid,
    write_marker_report,
    write_ocr_review,
    write_preprocess_review,
    write_run_index,
)
from court_ocr_extract.review_manifest import write_review_manifest
from court_ocr_extract.review_sampling import ReviewCandidate, select_review_sample
from court_ocr_extract.settings import get_settings
from court_ocr_extract.transfer import zip_debug_visual
from court_ocr_extract.validation import validate_extraction_payload
from court_ocr_extract.visual_debug import make_run_dir


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="court-ocr-extract")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_debug_render(subparsers)
    _add_debug_preprocess(subparsers)
    _add_debug_red_seal(subparsers)
    _add_debug_bbox(subparsers)
    _add_debug_ocr_review(subparsers)
    _add_debug_marker(subparsers)
    _add_ocr(subparsers)
    _add_preview_extraction(subparsers)
    _add_extract(subparsers)
    _add_qa(subparsers)
    _add_benchmark_ocr(subparsers)
    _add_benchmark_extractors(subparsers)
    _add_compare_pre_content(subparsers)
    _add_zip_debug_visual(subparsers)
    args = parser.parse_args(argv)
    args.func(args)


def _add_input_review_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", "--input-dir", dest="input_dir", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--review-sample-size", type=int, default=5)
    parser.add_argument("--review-seed", type=int, default=42)
    parser.add_argument("--review-mode", default="mixed")
    parser.add_argument(
        "--pages",
        default=None,
        help="Page range such as 1-3 or 2,4,6-8. Default/all means all pages.",
    )
    parser.add_argument("--output", default="outputs/debug_visual")
    parser.add_argument("--open", action="store_true")


def _add_debug_render(subparsers) -> None:
    parser = subparsers.add_parser("debug-render")
    _add_input_review_args(parser)
    parser.set_defaults(func=cmd_debug_render)


def _add_debug_preprocess(subparsers) -> None:
    parser = subparsers.add_parser("debug-preprocess")
    _add_input_review_args(parser)
    parser.add_argument("--deskew", choices=["off", "safe", "force"], default="off")
    parser.add_argument("--red-seal-removal", choices=["on", "off"], default="on")
    parser.add_argument(
        "--red-removal-mode",
        choices=["neutralize", "inpaint", "white_fill"],
        default="neutralize",
    )
    parser.add_argument("--text-enhance", choices=["off", "light", "medium", "strong"], default="light")
    parser.add_argument(
        "--preprocess-profile",
        choices=["conservative", "balanced", "aggressive"],
        default="conservative",
    )
    parser.add_argument(
        "--stamp-suppression",
        choices=["off", "conservative", "balanced", "aggressive"],
        default="balanced",
    )
    _add_stamp_erase_arg(parser)
    parser.set_defaults(func=cmd_debug_preprocess)


def _add_debug_red_seal(subparsers) -> None:
    parser = subparsers.add_parser("debug-red-seal")
    _add_input_review_args(parser)
    parser.set_defaults(func=cmd_debug_red_seal)


def _add_debug_bbox(subparsers) -> None:
    parser = subparsers.add_parser("debug-bbox")
    _add_input_review_args(parser)
    parser.add_argument("--ocr-backend", default=None)
    parser.set_defaults(func=cmd_debug_bbox)


def _add_debug_ocr_review(subparsers) -> None:
    parser = subparsers.add_parser("debug-ocr-review")
    _add_input_review_args(parser)
    parser.add_argument("--ocr-backend", default=None)
    _add_full_document_args(parser)
    _add_ocr_preprocess_args(parser)
    parser.set_defaults(func=cmd_debug_ocr_review, surya_startup_timeout_seconds=300)


def _add_debug_marker(subparsers) -> None:
    parser = subparsers.add_parser("debug-marker")
    parser.add_argument("--ocr-cache", required=True)
    parser.add_argument("--review-sample-size", type=int, default=5)
    parser.add_argument("--review-seed", type=int, default=42)
    parser.add_argument("--review-mode", default="mixed")
    parser.add_argument("--output", default="outputs/debug_visual")
    parser.add_argument("--open", action="store_true")
    parser.set_defaults(func=cmd_debug_marker)


def _add_ocr(subparsers) -> None:
    parser = subparsers.add_parser("ocr")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--cache-dir", default="outputs/ocr_cache")
    parser.add_argument("--ocr-backend", default=None)
    parser.add_argument("--fallback-ocr-backend", default="")
    parser.add_argument("--debug-visual", action="store_true")
    _add_full_document_args(parser)
    _add_ocr_preprocess_args(parser)
    parser.set_defaults(func=cmd_ocr, surya_startup_timeout_seconds=600)


def _add_full_document_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--full-document",
        action="store_true",
        help="Process all pages and do not stop/truncate at the content marker.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional maximum pages to process. Ignored when --full-document is set.",
    )


def _add_ocr_preprocess_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--use-preprocessed", action="store_true")
    parser.add_argument("--deskew", choices=["off", "safe", "force"], default="off")
    parser.add_argument("--red-seal-removal", choices=["on", "off"], default="on")
    parser.add_argument(
        "--red-removal-mode",
        choices=["neutralize", "inpaint", "white_fill"],
        default="neutralize",
    )
    parser.add_argument("--text-enhance", choices=["off", "light", "medium", "strong"], default="light")
    parser.add_argument(
        "--preprocess-profile",
        choices=["conservative", "balanced", "aggressive"],
        default="conservative",
    )
    parser.add_argument(
        "--stamp-suppression",
        choices=["off", "conservative", "balanced", "aggressive"],
        default="balanced",
    )
    parser.add_argument(
        "--ocr-stamp-filter",
        choices=["off", "conservative", "balanced", "aggressive"],
        default="balanced",
    )
    _add_stamp_erase_arg(parser)
    parser.add_argument("--surya-docker-binary", default=None)
    parser.add_argument("--check-surya-runtime", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-surya-runtime-preflight", action="store_true")
    parser.add_argument("--surya-runtime-check-gpu-container", action="store_true")
    parser.add_argument("--surya-runtime-timeout-seconds", type=int, default=30)
    parser.add_argument("--surya-startup-timeout-seconds", type=int, default=None)
    parser.add_argument("--stop-at-marker", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--marker-text", default=None)
    parser.add_argument("--marker-include-page", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--marker-trim-after-marker", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--ocr-page-batch-size", type=int, default=1)


def _add_stamp_erase_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--stamp-erase-mode",
        choices=["mask", "component_white_fill", "component_inpaint", "local_background"],
        default="component_white_fill",
    )


def _add_preview_extraction(subparsers) -> None:
    parser = subparsers.add_parser("preview-extraction")
    parser.add_argument("--ocr-cache", default=None)
    parser.add_argument("--input", "--input-dir", dest="input_dir", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--review-sample-size", type=int, default=5)
    parser.add_argument("--review-seed", type=int, default=42)
    parser.add_argument("--review-mode", default="mixed")
    parser.add_argument("--extractor", required=True)
    parser.add_argument("--output", default="outputs/debug_visual")
    parser.add_argument("--debug-json", action="store_true")
    parser.add_argument("--open", action="store_true")
    parser.set_defaults(func=cmd_preview_extraction)


def _add_extract(subparsers) -> None:
    parser = subparsers.add_parser("extract")
    parser.add_argument("--ocr-cache", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--extractor", required=True)
    parser.add_argument("--review-sample-size", type=int, default=5)
    parser.add_argument("--review-seed", type=int, default=42)
    parser.add_argument("--review-mode", default="mixed")
    parser.add_argument("--debug-json", action="store_true")
    parser.set_defaults(func=cmd_extract)


def _add_qa(subparsers) -> None:
    parser = subparsers.add_parser("qa-output")
    parser.add_argument("--excel", required=True)
    parser.set_defaults(func=cmd_qa_output)


def _add_benchmark_ocr(subparsers) -> None:
    parser = subparsers.add_parser("benchmark-ocr")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--backends", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--debug-visual", action="store_true")
    parser.add_argument("--review-sample-size", type=int, default=5)
    parser.add_argument("--review-mode", default="mixed")
    parser.set_defaults(func=cmd_benchmark_ocr)


def _add_benchmark_extractors(subparsers) -> None:
    parser = subparsers.add_parser("benchmark-extractors")
    parser.add_argument("--ocr-cache", default=None)
    parser.add_argument("--input-dir", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--extractors", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--debug-visual", action="store_true")
    parser.add_argument("--review-sample-size", type=int, default=5)
    parser.add_argument("--review-mode", default="mixed")
    parser.set_defaults(func=cmd_benchmark_extractors)


def _add_compare_pre_content(subparsers) -> None:
    parser = subparsers.add_parser("compare-pre-content")
    parser.add_argument("--ocr-cache-dir", required=True)
    parser.add_argument("--input-dir", default=None, help="Optional source directory for operator traceability; PDFs are not read by this command.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--strategies", default="hybrid_rule_llm,llm_only")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--open", action="store_true")
    parser.set_defaults(func=cmd_compare_pre_content)


def _add_zip_debug_visual(subparsers) -> None:
    parser = subparsers.add_parser("zip-debug-visual")
    parser.add_argument("--run-id", default="latest")
    parser.add_argument("--output", required=True)
    parser.add_argument("--debug-visual-dir", default="outputs/debug_visual")
    parser.set_defaults(func=cmd_zip_debug_visual)


def cmd_debug_render(args) -> None:
    settings = get_settings()
    run_dir = make_run_dir(args.output)
    cases = _sample_case_files(args)
    pages = parse_page_range(args.pages)
    image_cases = []
    for case in track(cases, "Rendering cases", total=len(cases)):
        case_dir = run_dir / case.case_id / "01_rendered"
        rendered = render_pdf_pages(case.path, case_dir, dpi=settings.ocr_dpi, page_numbers=pages)
        image_cases.append({"case_id": case.case_id, "images": [(f"page {p.page_number}", p.image_path) for p in rendered]})
    grid = write_image_grid(run_dir / "render_review_grid.html", title="Render Review", cases=image_cases, base_dir=run_dir)
    index = write_run_index(run_dir, {"render review": grid})
    _maybe_open(index, args.open)
    _print_phase_result("debug-render", run_dir)


def cmd_debug_preprocess(args) -> None:
    settings = get_settings()
    run_dir = make_run_dir(args.output)
    cases = _sample_case_files(args)
    pages = parse_page_range(args.pages)
    review_cases = []
    for case in track(cases, "Preprocessing cases", total=len(cases)):
        rendered = render_pdf_pages(case.path, run_dir / case.case_id / "01_rendered", dpi=settings.ocr_dpi, page_numbers=pages)
        review_pages = []
        for page in rendered:
            page_dir = run_dir / case.case_id / "02_preprocess" / f"page_{page.page_number:03d}"
            after = page_dir / "final_preprocessed.png"
            compare = page_dir / "before_after_compare.png"
            red_mask = page_dir / "red_mask.png"
            black_text_protection = page_dir / "black_text_protection_mask.png"
            seal_removed = page_dir / "seal_removed.png"
            text_enhanced = page_dir / "text_enhanced.png"
            final_candidate = page_dir / "final_preprocessed_candidate.png"
            stamp_suppression_mask = page_dir / "stamp_suppression_mask.png"
            object_seed_mask = page_dir / "object_seed_mask.png"
            stamp_object_mask = page_dir / "stamp_object_mask.png"
            stamp_object_erased = page_dir / "stamp_object_erased.png"
            ocr_input_suppressed = page_dir / "ocr_input_stamp_suppressed.png"
            metadata_path = page_dir / "metadata.json"
            page_dir.mkdir(parents=True, exist_ok=True)
            metadata: dict[str, Any] = {"page_number": page.page_number}
            preprocess_image(
                page.image_path,
                after,
                remove_red_seal=args.red_seal_removal == "on",
                intermediate_path=seal_removed,
                red_mask_path=red_mask,
                black_text_protection_path=black_text_protection,
                red_removal_mode=args.red_removal_mode,
                text_enhanced_path=text_enhanced,
                text_enhance_mode=args.text_enhance,
                deskew_mode=args.deskew,
                preprocess_profile=args.preprocess_profile,
                metadata=metadata,
            )
            if after.exists():
                shutil.copy2(after, final_candidate)
            candidate_input = final_candidate if final_candidate.exists() else after
            metadata.update(
                suppress_stamp_for_ocr(
                    candidate_input,
                    red_mask,
                    black_text_protection,
                    ocr_input_suppressed,
                    stamp_suppression_mask,
                    mode=args.stamp_suppression,
                    erase_mode=args.stamp_erase_mode,
                    stamp_object_mask_path=stamp_object_mask,
                    stamp_object_erased_path=stamp_object_erased,
                    object_seed_mask_path=object_seed_mask,
                    final_selected_path=after,
                    candidate_paths={
                        "seal_removed": seal_removed,
                        "text_enhanced": text_enhanced,
                    },
                )
            )
            metadata["page_number"] = page.page_number
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            make_before_after_compare(page.image_path, after, compare)
            page_images = [("original", page.image_path)]
            if red_mask.exists():
                page_images.append(("red_mask", red_mask))
            if black_text_protection.exists():
                page_images.append(("black_text_protection_mask", black_text_protection))
            if seal_removed.exists():
                page_images.append(("seal_removed", seal_removed))
            if text_enhanced.exists():
                page_images.append(("text_enhanced", text_enhanced))
            if stamp_suppression_mask.exists():
                page_images.append(("stamp_suppression_mask", stamp_suppression_mask))
            if object_seed_mask.exists():
                page_images.append(("object_seed_mask", object_seed_mask))
            if stamp_object_mask.exists():
                page_images.append(("stamp_object_mask", stamp_object_mask))
            if stamp_object_erased.exists():
                page_images.append(("stamp_object_erased", stamp_object_erased))
            if ocr_input_suppressed.exists():
                page_images.append(("ocr_input_stamp_suppressed", ocr_input_suppressed))
            if final_candidate.exists():
                page_images.append(("final_preprocessed_candidate", final_candidate))
            page_images.extend([("final_preprocessed", after), ("before_after_compare", compare)])
            review_pages.append({"metadata": metadata, "images": page_images})
        review_cases.append({"case_id": case.case_id, "pages": review_pages})
    grid = write_preprocess_review(run_dir / "preprocess_review_grid.html", cases=review_cases, base_dir=run_dir)
    index = write_run_index(run_dir, {"preprocess review": grid})
    _maybe_open(index, args.open)
    _print_phase_result("debug-preprocess", run_dir)


def cmd_debug_red_seal(args) -> None:
    settings = get_settings()
    run_dir = make_run_dir(args.output)
    cases = _sample_case_files(args)
    pages = parse_page_range(args.pages)
    image_cases = []
    for case in track(cases, "Red seal review", total=len(cases)):
        rendered = render_pdf_pages(case.path, run_dir / case.case_id / "01_rendered", dpi=settings.ocr_dpi, page_numbers=pages)
        images = []
        for page in rendered:
            debug = remove_red_seal_debug(page.image_path, run_dir / case.case_id / "03_red_seal_removal" / f"page_{page.page_number:03d}")
            images.extend([(f"page {page.page_number} {label}", path) for label, path in debug.items()])
        image_cases.append({"case_id": case.case_id, "images": images})
    grid = write_image_grid(run_dir / "red_seal_review_grid.html", title="Red Seal Review", cases=image_cases, base_dir=run_dir)
    index = write_run_index(run_dir, {"red seal review": grid})
    _maybe_open(index, args.open)
    _print_phase_result("debug-red-seal", run_dir)


def cmd_debug_bbox(args) -> None:
    run_dir = make_run_dir(args.output)
    records = _run_sample_ocr(args, run_dir)
    report = write_marker_report(run_dir / "bbox_report.html", records)
    index = write_run_index(run_dir, {"bbox report": report})
    _maybe_open(index, args.open)
    print("BBox report created. Backends without bbox return a report instead of invented boxes.")


def cmd_debug_ocr_review(args) -> None:
    run_dir = make_run_dir(args.output)
    records = _run_sample_ocr(args, run_dir)
    review = write_ocr_review(run_dir / "ocr_review.html", records, base_dir=run_dir)
    marker = write_marker_report(run_dir / "marker_report.html", records)
    index = write_run_index(run_dir, {"ocr review": review, "marker report": marker})
    _maybe_open(index, args.open)
    _print_phase_result("debug-ocr-review", run_dir)


def cmd_debug_marker(args) -> None:
    run_dir = make_run_dir(args.output)
    records = _sample_records(read_ocr_cache_dir(args.ocr_cache), args)
    report = write_marker_report(run_dir / "marker_report.html", records)
    index = write_run_index(run_dir, {"marker report": report})
    _maybe_open(index, args.open)
    _print_phase_result("debug-marker", run_dir)


def cmd_ocr(args) -> None:
    settings = get_settings()
    backend = get_ocr_backend(args.ocr_backend, settings)
    status = backend.check_available()
    if not status.available:
        raise RuntimeError(status.reason)
    cache_dir = Path(args.cache_dir)
    debug_run_dir = make_run_dir(settings.debug_visual_dir) if args.debug_visual else None
    _run_surya_runtime_preflight(args, backend, output_dir=debug_run_dir)
    paths = discover_pdfs(args.input_dir, limit=args.limit)
    cases = case_files_for_paths(paths)
    max_pages = _resolve_ocr_page_limit(args, settings)
    stop_marker = _resolve_stop_marker(args, settings)
    records: list[OCRCacheRecord] = []
    for case in track(cases, "OCR cases", total=len(cases)):
        work_dir = debug_run_dir / case.case_id if debug_run_dir else None
        try:
            result = _run_ocr_backend(
                backend,
                case.path,
                max_pages=max_pages,
                stop_marker=stop_marker,
                debug_visual=bool(debug_run_dir),
                work_dir=work_dir,
                preprocess_options=_ocr_preprocess_options(args),
                runtime_options=_surya_runtime_options(args),
            )
        except Exception:
            if not args.fallback_ocr_backend:
                raise
            fallback = get_ocr_backend(args.fallback_ocr_backend, settings)
            result = _run_ocr_backend(
                fallback,
                case.path,
                max_pages=max_pages,
                stop_marker=stop_marker,
                debug_visual=bool(debug_run_dir),
                work_dir=work_dir,
                preprocess_options=_ocr_preprocess_options(args),
                runtime_options=_surya_runtime_options(args),
            )
        record = OCRCacheRecord(case.case_id, case.source_index, case.pdf_hash, result)
        write_ocr_cache_record(record, cache_dir)
        records.append(record)
        _print_ocr_case_summary(case.case_id, result, cache_dir, work_dir)
    print("OCR cache finished")
    print(f"PDFs processed: {len(records)}")
    print(f"OCR success: {sum(1 for record in records if record.result.status == 'success')}")
    print(f"Marker found: {sum(1 for record in records if record.result.marker_found)}")
    print(f"OCR cache: {cache_dir}")


def _print_ocr_case_summary(case_id: str, result: OCRResult, cache_dir: Path, work_dir: Path | None) -> None:
    total_lines = sum(len(page.lines) for page in result.pages)
    low_confidence = 0
    for page in result.pages:
        for line in page.lines:
            confidence = line.get("confidence")
            if confidence is not None and confidence < 0.5:
                low_confidence += 1
    warning_pages = sum(1 for page in result.pages if page.blocks and page.blocks[0].get("warnings"))
    print(f"Case: {case_id}")
    print(f"Backend: {result.backend}")
    print(f"Pages processed: {result.pages_processed}")
    print(f"Total lines: {total_lines}")
    print(f"Pages with warnings: {warning_pages}")
    print(f"Low confidence lines: {low_confidence}")
    print(f"Marker found: {'yes' if result.marker_found else 'no'}")
    early_stop = result.metadata.get("early_stop", {})
    print(f"Early stop triggered: {'yes' if early_stop.get('triggered') else 'no'}")
    print(f"Pages total: {result.metadata.get('pages_total', result.pages_processed)}")
    print(f"Pages skipped after marker: {early_stop.get('pages_skipped_after_marker', 0)}")
    print(f"Output OCR cache: {cache_dir}")
    if work_dir:
        surya_dir = work_dir / "ocr_surya"
        if surya_dir.exists():
            print(f"Output debug HTML: {surya_dir / 'index.html'}")
            print(f"Output bbox directory: {surya_dir}")


def cmd_preview_extraction(args) -> None:
    run_dir = make_run_dir(args.output)
    if not args.ocr_cache:
        _cmd_preview_direct_vision(args, run_dir)
        return
    records = read_ocr_cache_dir(args.ocr_cache)
    debug_dir = None
    if args.debug_json:
        debug_dir = Path("outputs/extraction_draft") / run_dir.name
    drafts = extract_from_ocr_cache_records(records, extractor_name=args.extractor, debug_json_dir=debug_dir)
    selected = _sample_drafts(drafts, args)
    selected_records = [record for record in records if record.case_id in {item["case_id"] for item in selected}]
    preview = write_extraction_preview(selected, selected_records, run_dir / "extraction_preview")
    manifest_candidates = select_review_sample(review_candidates_from_drafts(drafts), sample_size=args.review_sample_size, seed=args.review_seed, mode=args.review_mode)
    write_review_manifest(manifest_candidates, run_dir / "review_sample_manifest.xlsx", ocr_backend=_ocr_backend_name(records), extractor_backend=args.extractor)
    index = write_run_index(run_dir, {"extraction preview": preview})
    _maybe_open(index, args.open)
    _print_phase_result("preview-extraction", run_dir)


def _cmd_preview_direct_vision(args, run_dir: Path) -> None:
    if not args.input_dir:
        raise RuntimeError("Use --ocr-cache or --input for preview-extraction.")
    settings = get_settings()
    extractor = get_extractor_backend(args.extractor, settings)
    status = extractor.check_available()
    if not status.available:
        raise RuntimeError(status.reason)
    if not hasattr(extractor, "extract_from_pdf"):
        raise RuntimeError("Selected extractor does not support direct vision PDF preview.")
    cases = _sample_case_files(args)
    drafts = []
    for case in track(cases, "Direct vision extraction", total=len(cases)):
        try:
            payload = extractor.extract_from_pdf(case.path, case_id=case.case_id, max_pages=settings.max_pages_before_marker)
            payload = validate_extraction_payload(payload)
            status_value = "success"
            error = None
        except Exception as exc:
            payload = validate_extraction_payload({"case": {}, "participants": [], "document_warnings": [str(exc)]})
            status_value = "failed"
            error = str(exc)
        drafts.append(
            {
                "case_id": case.case_id,
                "source_index": case.source_index,
                "ocr_backend": "direct_vision",
                "extractor_backend": args.extractor,
                "marker_found": False,
                "status": status_value,
                "error": error,
                "payload": payload,
            }
        )
    preview = write_extraction_preview(drafts, [], run_dir / "extraction_preview")
    manifest_candidates = review_candidates_from_drafts(drafts)
    write_review_manifest(manifest_candidates, run_dir / "review_sample_manifest.xlsx", ocr_backend="direct_vision", extractor_backend=args.extractor)
    index = write_run_index(run_dir, {"extraction preview": preview})
    _maybe_open(index, args.open)
    _print_phase_result("preview-extraction", run_dir)


def cmd_extract(args) -> None:
    records = read_ocr_cache_dir(args.ocr_cache)
    run_dir = make_run_dir("outputs/debug_visual")
    debug_dir = Path("outputs/extraction_draft") / run_dir.name if args.debug_json else None
    drafts = extract_from_ocr_cache_records(records, extractor_name=args.extractor, debug_json_dir=debug_dir)
    selected = _sample_drafts(drafts, args)
    selected_records = [record for record in records if record.case_id in {item["case_id"] for item in selected}]
    preview = write_extraction_preview(selected, selected_records, run_dir / "extraction_preview")
    summary = build_run_summary(drafts)
    summary["Debug visual run id"] = run_dir.name
    excel = write_excel(drafts, args.output, run_summary=summary)
    write_run_index(run_dir, {"extraction preview": preview})
    print("Extraction finished")
    print(f"Rows extracted: {sum(len(item['payload'].get('participants', [])) or 1 for item in drafts)}")
    print(f"Rows need review: {sum(1 for item in drafts if item['payload'].get('document_warnings'))}")
    print(f"Excel: {excel}")
    print(f"Extraction preview: {preview}")


def cmd_qa_output(args) -> None:
    print_safe_qa(qa_excel(args.excel))


def cmd_benchmark_ocr(args) -> None:
    settings = get_settings()
    paths = discover_pdfs(args.input_dir, limit=args.limit)
    cases = case_files_for_paths(paths)
    rows = []
    for backend_name in [item.strip() for item in args.backends.split(",") if item.strip()]:
        backend = get_ocr_backend(backend_name, settings)
        status = backend.check_available()
        successes = failures = marker_found = 0
        notes = []
        if not status.available:
            notes.append(status.reason)
        else:
            for case in track(cases, f"Benchmark OCR {backend_name}", total=len(cases)):
                try:
                    result = backend.ocr_pdf_prefix(case.path, settings.max_pages_before_marker, settings.stop_marker)
                    successes += result.status == "success"
                    marker_found += result.marker_found
                except Exception as exc:
                    failures += 1
                    notes.append(type(exc).__name__)
        rows.append([backend_name, len(cases), successes, failures, marker_found, "", "", "", "; ".join(sorted(set(notes)))])
    _write_benchmark(args.output, "OCR_BENCHMARK", ["BACKEND", "TỔNG PDF", "SỐ FILE THÀNH CÔNG", "SỐ FILE LỖI", "MARKER FOUND", "AVG SECONDS/FILE", "ESTIMATED COST", "SỐ FILE CẦN REVIEW", "GHI CHÚ"], rows)
    print(f"OCR benchmark: {args.output}")


def cmd_benchmark_extractors(args) -> None:
    settings = get_settings()
    records = read_ocr_cache_dir(args.ocr_cache) if args.ocr_cache else []
    cases = case_files_for_paths(discover_pdfs(args.input_dir, limit=args.limit)) if args.input_dir else []
    rows = []
    for extractor_name in [item.strip() for item in args.extractors.split(",") if item.strip()]:
        try:
            if extractor_name.startswith("direct_vision"):
                if not cases:
                    raise RuntimeError("Direct vision benchmark requires --input-dir.")
                extractor = get_extractor_backend(extractor_name, settings)
                direct_status = extractor.check_available()
                if not direct_status.available:
                    raise RuntimeError(direct_status.reason)
                drafts = []
                for case in track(cases, f"Benchmark {extractor_name}", total=len(cases)):
                    payload = extractor.extract_from_pdf(
                        case.path,
                        case_id=case.case_id,
                        max_pages=settings.max_pages_before_marker,
                    )
                    drafts.append(
                        {
                            "case_id": case.case_id,
                            "source_index": case.source_index,
                            "status": "success",
                            "marker_found": False,
                            "payload": validate_extraction_payload(payload),
                        }
                    )
            else:
                if not records:
                    raise RuntimeError("Text extractor benchmark requires --ocr-cache.")
                drafts = extract_from_ocr_cache_records(records, extractor_name=extractor_name)
            success = sum(1 for item in drafts if item["status"] == "success")
            review = sum(1 for item in drafts if item["payload"].get("document_warnings"))
            note = ""
        except Exception as exc:
            success = 0
            review = len(records) or len(cases)
            note = str(exc)
        total = len(records) if records else len(cases)
        rows.append([extractor_name, total, success, total - success, review, note])
    _write_benchmark(args.output, "EXTRACTOR_BENCHMARK", ["EXTRACTOR", "TỔNG PDF", "SỐ FILE THÀNH CÔNG", "SỐ FILE LỖI", "SỐ FILE CẦN REVIEW", "GHI CHÚ"], rows)
    print(f"Extractor benchmark: {args.output}")


def cmd_compare_pre_content(args) -> None:
    records = read_ocr_cache_dir(args.ocr_cache_dir)
    if not records:
        raise RuntimeError(f"No OCR cache records found in: {args.ocr_cache_dir}")
    strategies = [value.strip() for value in args.strategies.split(",") if value.strip()]
    summary = run_pre_content_ab_test(
        records,
        output_dir=args.output_dir,
        settings=get_settings(),
        strategies=strategies,
        limit=args.limit,
    )
    index = Path(args.output_dir) / "index.html"
    _maybe_open(index, args.open)
    print(f"Pre-content A/B cases: {summary['case_count']}")
    print(f"Judgment benchmark cases: {summary['judgment_benchmark_count']}")
    print(f"Output: {index}")


def cmd_zip_debug_visual(args) -> None:
    output = zip_debug_visual(args.run_id, debug_visual_dir=args.debug_visual_dir, output_path=args.output)
    print(f"Debug visual zip: {output}")


def _sample_case_files(args) -> list:
    paths = discover_pdfs(args.input_dir, limit=args.limit)
    cases = case_files_for_paths(paths)
    candidates = [ReviewCandidate(case.case_id, case.source_index) for case in cases]
    selected = select_review_sample(candidates, sample_size=args.review_sample_size, seed=args.review_seed, mode=args.review_mode)
    selected_ids = {item.case_id for item in selected}
    return [case for case in cases if case.case_id in selected_ids]


def _run_sample_ocr(args, run_dir: Path) -> list[OCRCacheRecord]:
    settings = get_settings()
    backend = get_ocr_backend(args.ocr_backend, settings)
    status = backend.check_available()
    if not status.available:
        raise RuntimeError(status.reason)
    _run_surya_runtime_preflight(args, backend, output_dir=run_dir)
    cases = _sample_case_files(args)
    max_pages = _resolve_ocr_page_limit(args, settings)
    stop_marker = _resolve_stop_marker(args, settings)
    records: list[OCRCacheRecord] = []
    for case in track(cases, "OCR review cases", total=len(cases)):
        result = _run_ocr_backend(
            backend,
            case.path,
            max_pages=max_pages,
            stop_marker=stop_marker,
            debug_visual=True,
            work_dir=run_dir / case.case_id,
            preprocess_options=_ocr_preprocess_options(args),
            runtime_options=_surya_runtime_options(args),
        )
        records.append(OCRCacheRecord(case.case_id, case.source_index, case.pdf_hash, result))
    return records


def _resolve_ocr_page_limit(args, settings) -> int | None:
    if getattr(args, "full_document", False):
        return None
    page_spec = getattr(args, "pages", None)
    if page_spec:
        pages = parse_page_range(page_spec)
        if pages:
            expected = list(range(1, max(pages) + 1))
            if pages != expected:
                raise ValueError(
                    "OCR review currently supports --pages only as a prefix starting at page 1 "
                    "(for example: --pages 1 or --pages 1-3)."
                )
            return max(pages)
    max_pages = getattr(args, "max_pages", None)
    if max_pages is not None:
        return max_pages
    return None


def _ocr_preprocess_options(args) -> dict[str, Any] | None:
    if getattr(args, "surya_docker_binary", None):
        os.environ["SURYA_DOCKER_BINARY"] = args.surya_docker_binary
    if not getattr(args, "use_preprocessed", False):
        return None
    return {
        "deskew": args.deskew,
        "red_seal_removal": args.red_seal_removal == "on",
        "red_removal_mode": args.red_removal_mode,
        "text_enhance": args.text_enhance,
        "preprocess_profile": args.preprocess_profile,
        "stamp_suppression": args.stamp_suppression,
        "stamp_erase_mode": args.stamp_erase_mode,
        "ocr_stamp_filter": args.ocr_stamp_filter,
    }


def _surya_runtime_options(args) -> dict[str, Any]:
    return {
        "docker_binary": getattr(args, "surya_docker_binary", None),
        "startup_timeout_seconds": int(getattr(args, "surya_startup_timeout_seconds", None) or 600),
        "container_spawn_check_seconds": min(
            120,
            max(1, int(getattr(args, "surya_startup_timeout_seconds", None) or 600) // 5),
        ),
        "marker_include_page": bool(getattr(args, "marker_include_page", True)),
        "marker_trim_after_marker": bool(getattr(args, "marker_trim_after_marker", True)),
        "ocr_page_batch_size": max(1, int(getattr(args, "ocr_page_batch_size", 1))),
    }


def _run_surya_runtime_preflight(args, backend, *, output_dir: Path | None) -> dict[str, Any] | None:
    if getattr(backend, "name", "") not in {"surya", "surya_optional"}:
        return None
    if getattr(args, "skip_surya_runtime_preflight", False):
        print("Surya runtime preflight skipped by explicit user option.")
        return {"ok": None, "skipped": True}
    diagnostics = collect_surya_runtime_diagnostics(
        check_gpu_container=bool(getattr(args, "surya_runtime_check_gpu_container", False)),
        docker_binary=getattr(args, "surya_docker_binary", None),
        runtime_timeout_seconds=int(getattr(args, "surya_runtime_timeout_seconds", 30)),
        gpu_container_timeout_seconds=int(getattr(args, "surya_runtime_timeout_seconds", 30)),
    )
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "surya_runtime_preflight.json").write_text(
            json.dumps(diagnostics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if not diagnostics["ok"]:
        docker = diagnostics.get("docker", {})
        api = diagnostics.get("surya_api", {})
        raise RuntimeError(
            "Surya runtime preflight failed before OCR predictor call. "
            f"Docker binary: {docker.get('binary') or 'not found'}; "
            f"Docker error: {docker.get('error') or 'none'}; "
            f"Surya API: {api.get('kind', 'unknown')}; "
            f"GPU container checked: {diagnostics.get('gpu_container', {}).get('checked', False)}. "
            "Run `python -m scripts.check_surya_runtime_backend --check-gpu-container` for full diagnostics."
        )
    print(
        "Surya runtime preflight passed: "
        f"docker={diagnostics['docker'].get('binary')}, "
        f"api={diagnostics['surya_api'].get('kind')}, "
        f"gpu_checked={diagnostics['gpu_container'].get('checked', False)}"
    )
    return diagnostics


def _run_ocr_backend(
    backend,
    pdf_path: Path,
    *,
    max_pages: int | None,
    stop_marker: str,
    debug_visual: bool,
    work_dir: Path | None,
    preprocess_options: dict[str, Any] | None,
    runtime_options: dict[str, Any] | None = None,
) -> OCRResult:
    runtime_options = runtime_options or {}
    if getattr(backend, "name", "") not in {"surya", "surya_optional"}:
        runtime_options = {}
    else:
        signature = inspect.signature(backend.ocr_pdf_prefix)
        accepts_kwargs = any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )
        if not accepts_kwargs:
            runtime_options = {
                key: value for key, value in runtime_options.items() if key in signature.parameters
            }
    if preprocess_options is None:
        return backend.ocr_pdf_prefix(
            pdf_path,
            max_pages=max_pages,
            stop_marker=stop_marker,
            debug_visual=debug_visual,
            work_dir=work_dir,
            **runtime_options,
        )
    if getattr(backend, "name", "") not in {"surya", "surya_optional"}:
        raise RuntimeError("--use-preprocessed currently requires the Surya OCR backend.")
    return backend.ocr_pdf_prefix(
        pdf_path,
        max_pages=max_pages,
        stop_marker=stop_marker,
        debug_visual=debug_visual,
        work_dir=work_dir,
        preprocess_options=preprocess_options,
        **runtime_options,
    )


def _resolve_stop_marker(args, settings) -> str:
    if getattr(args, "full_document", False) or not getattr(args, "stop_at_marker", True):
        return ""
    return getattr(args, "marker_text", None) or settings.stop_marker


def _sample_records(records: list[OCRCacheRecord], args) -> list[OCRCacheRecord]:
    candidates = [
        ReviewCandidate(
            case_id=record.case_id,
            source_index=record.source_index,
            status=record.result.status,
            marker_found=record.result.marker_found,
            warnings_count=len(record.result.warnings),
        )
        for record in records
    ]
    selected = select_review_sample(candidates, sample_size=args.review_sample_size, seed=args.review_seed, mode=args.review_mode)
    selected_ids = {item.case_id for item in selected}
    return [record for record in records if record.case_id in selected_ids]


def _sample_drafts(drafts: list[dict[str, Any]], args) -> list[dict[str, Any]]:
    candidates = select_review_sample(review_candidates_from_drafts(drafts), sample_size=args.review_sample_size, seed=args.review_seed, mode=args.review_mode)
    selected_ids = {item.case_id for item in candidates}
    return [draft for draft in drafts if draft["case_id"] in selected_ids]


def _ocr_backend_name(records: list[OCRCacheRecord]) -> str:
    return ", ".join(sorted({record.result.backend for record in records}))


def _write_benchmark(output_path: str | Path, sheet_name: str, headers: list[str], rows: list[list[Any]]) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(output_path)


def _maybe_open(path: Path, enabled: bool) -> None:
    if enabled:
        webbrowser.open(path.resolve().as_uri())


def _print_phase_result(name: str, run_dir: Path) -> None:
    print(f"{name} done")
    print(f"Visual/debug outputs: {run_dir}")


if __name__ == "__main__":
    main()
