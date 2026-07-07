from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from court_ocr_extract.extractors import get_extractor_backend
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.progress import track
from court_ocr_extract.review_sampling import ReviewCandidate
from court_ocr_extract.validation import min_participant_confidence, validate_extraction_payload


def extract_from_ocr_cache_records(
    records: list[OCRCacheRecord],
    *,
    extractor_name: str,
    debug_json_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    extractor = get_extractor_backend(extractor_name)
    status = extractor.check_available()
    if not status.available:
        raise RuntimeError(status.reason)

    debug_dir = Path(debug_json_dir) if debug_json_dir else None
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)

    drafts: list[dict[str, Any]] = []
    for record in track(records, "Extracting", total=len(records)):
        try:
            payload = extractor.extract_from_text(record.result.text, case_id=record.case_id)
            payload = validate_extraction_payload(payload)
            status_value = "success"
            error = None
        except Exception as exc:
            payload = validate_extraction_payload({"case": {}, "participants": [], "document_warnings": [str(exc)]})
            status_value = "failed"
            error = str(exc)
        draft = {
            "case_id": record.case_id,
            "source_index": record.source_index,
            "ocr_backend": record.result.backend,
            "extractor_backend": extractor_name,
            "marker_found": record.result.marker_found,
            "status": status_value,
            "error": error,
            "payload": payload,
        }
        drafts.append(draft)
        if debug_dir:
            (debug_dir / f"{record.case_id}.json").write_text(
                json.dumps(draft, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    if debug_dir:
        _write_draft_jsonl(drafts, debug_dir / "draft_internal.jsonl")
        _write_draft_summary_xlsx(drafts, debug_dir / "draft_summary.xlsx")
    return drafts


def review_candidates_from_drafts(drafts: list[dict[str, Any]]) -> list[ReviewCandidate]:
    candidates = []
    for item in drafts:
        payload = item.get("payload", {})
        warnings_count = len(payload.get("document_warnings", []))
        warnings_count += sum(len(part.get("warnings", [])) for part in payload.get("participants", []))
        candidates.append(
            ReviewCandidate(
                case_id=item["case_id"],
                source_index=item.get("source_index", 0),
                status=item.get("status", "failed"),
                marker_found=bool(item.get("marker_found")),
                warnings_count=warnings_count,
                participants_count=len(payload.get("participants", [])),
                min_confidence=min_participant_confidence(payload),
            )
        )
    return candidates


def _write_draft_jsonl(drafts: list[dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        for draft in drafts:
            handle.write(json.dumps(draft, ensure_ascii=False) + "\n")


def _write_draft_summary_xlsx(drafts: list[dict[str, Any]], output_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "DRAFT_SUMMARY"
    sheet.append(
        [
            "CASE_ID",
            "SOURCE_INDEX",
            "OCR_BACKEND",
            "EXTRACTOR_BACKEND",
            "MARKER_FOUND",
            "STATUS",
            "PARTICIPANTS_COUNT",
            "DOCUMENT_WARNINGS_COUNT",
        ]
    )
    for draft in drafts:
        payload = draft.get("payload", {})
        sheet.append(
            [
                draft.get("case_id"),
                draft.get("source_index"),
                draft.get("ocr_backend"),
                draft.get("extractor_backend"),
                bool(draft.get("marker_found")),
                draft.get("status"),
                len(payload.get("participants", [])),
                len(payload.get("document_warnings", [])),
            ]
        )
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = min(
            max(len(str(column[0].value)) + 4, 14),
            34,
        )
    workbook.save(output_path)
