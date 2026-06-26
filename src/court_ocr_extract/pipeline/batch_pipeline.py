from __future__ import annotations

import logging
from pathlib import Path

from court_ocr_extract.config import Settings, get_settings
from court_ocr_extract.export.excel_writer import write_excel_from_results
from court_ocr_extract.file_utils import sha256_file, short_hash, write_json
from court_ocr_extract.models import ExtractionResult, model_to_dict
from court_ocr_extract.pipeline.single_file_pipeline import process_pdf
from court_ocr_extract.privacy import redact_sensitive_payload


LOGGER = logging.getLogger(__name__)


def process_batch(
    input_dir: str | Path,
    *,
    output_excel: str | Path | None = None,
    sample_size: int | None = None,
    limit: int | None = None,
    debug_limit: int | None = None,
    force: bool = False,
    settings: Settings | None = None,
    **process_kwargs,
) -> dict:
    settings = settings or get_settings()
    input_dir = Path(input_dir)
    pdf_paths = sorted(input_dir.glob("*.pdf"))
    if debug_limit:
        pdf_paths = pdf_paths[:debug_limit]
    if limit:
        pdf_paths = pdf_paths[:limit]
    if sample_size:
        import random

        pdf_paths = random.sample(pdf_paths, min(sample_size, len(pdf_paths)))

    results: list[ExtractionResult] = []
    skipped: list[str] = []
    failures: list[dict[str, str]] = []

    total = len(pdf_paths)
    for index, pdf_path in enumerate(pdf_paths, start=1):
        file_id = short_hash(sha256_file(pdf_path))
        checkpoint = settings.checkpoint_dir / f"{file_id}.json"
        if checkpoint.exists() and not force:
            skipped.append(file_id)
            print(f"[batch] skip {index}/{total} file_id={file_id} checkpoint_exists", flush=True)
            continue
        try:
            print(f"[batch] start {index}/{total} file_id={file_id}", flush=True)
            process_result = process_pdf(pdf_path, force=force, settings=settings, **process_kwargs)
            results.append(process_result.result)
            pages_ocr = process_result.metadata.pages_ocr if process_result.metadata else "?"
            print(
                f"[batch] done {index}/{total} file_id={file_id} pages_ocr={pages_ocr}",
                flush=True,
            )
        except Exception as exc:
            LOGGER.exception("Failed processing file_id=%s", file_id)
            failures.append({"file_id": file_id, "error": str(exc)})
            print(f"[batch] failed {index}/{total} file_id={file_id}: {exc}", flush=True)

    output_excel = Path(output_excel) if output_excel else settings.excel_dir / "batch_results.xlsx"
    if results:
        try:
            write_excel_from_results(results, output_excel)
        except ModuleNotFoundError:
            output_excel = None

    summary_json = settings.json_dir / "batch_summary.json"
    summary = {
        "total": len(pdf_paths),
        "success": len(results),
        "skipped": len(skipped),
        "failed": len(failures),
        "skipped_file_ids": skipped,
        "combined_excel": str(output_excel) if output_excel else None,
        "summary_json": str(summary_json),
        "failures": failures,
        "results": [
            redact_sensitive_payload(
                model_to_dict(result),
                include_sensitive=settings.persist_sensitive_json_text or settings.debug_sensitive,
            )
            for result in results
        ],
    }
    write_json(summary_json, summary)
    return summary
