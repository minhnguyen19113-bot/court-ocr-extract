from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text
from court_ocr_extract.ocr_backends.base import OCRResult
from court_ocr_extract.source_region_policy import DECISION_TAIL


DEFAULT_DECISION_HEADING_VARIANTS = (
    "QUYẾT ĐỊNH",
    "QUYẾT ĐỊNH CỦA TÒA ÁN",
    "VÌ CÁC LẼ TRÊN, QUYẾT ĐỊNH",
)
DECISION_TAIL_CACHE_SCHEMA_VERSION = 1


@dataclass
class DecisionTailRecord:
    case_id: str
    source_index: int
    pdf_hash: str | None
    backend: str
    pages_total: int
    scanned_page_numbers: list[int]
    scan_batches: list[list[int]]
    heading_found: bool
    heading_page: int | None
    heading_line_id: str | None
    heading_text: str | None
    text: str
    lines: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    status: str = "success"
    schema_version: int = DECISION_TAIL_CACHE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DecisionTailRecord":
        return cls(
            case_id=str(payload["case_id"]),
            source_index=int(payload.get("source_index", 0)),
            pdf_hash=payload.get("pdf_hash"),
            backend=str(payload.get("backend") or ""),
            pages_total=int(payload.get("pages_total", 0)),
            scanned_page_numbers=[int(value) for value in payload.get("scanned_page_numbers", [])],
            scan_batches=[
                [int(value) for value in batch]
                for batch in payload.get("scan_batches", [])
            ],
            heading_found=bool(payload.get("heading_found", False)),
            heading_page=payload.get("heading_page"),
            heading_line_id=payload.get("heading_line_id"),
            heading_text=payload.get("heading_text"),
            text=str(payload.get("text") or ""),
            lines=[dict(line) for line in payload.get("lines", []) if isinstance(line, dict)],
            warnings=[str(value) for value in payload.get("warnings", []) if value],
            status=str(payload.get("status") or "partial"),
            schema_version=int(payload.get("schema_version", DECISION_TAIL_CACHE_SCHEMA_VERSION)),
        )


OCRBatchCallable = Callable[[list[int]], OCRResult]


def scan_decision_tail(
    *,
    case_id: str,
    source_index: int,
    pdf_hash: str | None,
    backend: str,
    pages_total: int,
    ocr_batch: OCRBatchCallable,
    batch_size: int,
    max_scan_pages: int,
    heading_variants: tuple[str, ...] = DEFAULT_DECISION_HEADING_VARIANTS,
) -> DecisionTailRecord:
    if pages_total < 1:
        raise ValueError("pages_total must be positive")
    batch_size = max(1, int(batch_size))
    if max_scan_pages is None or int(max_scan_pages) < 1:
        raise ValueError(
            "max_scan_pages must be a positive finite limit; full-document fallback is disabled"
        )
    scan_limit = min(pages_total, int(max_scan_pages))
    normalized_headings = {fold_text(value).strip(" .,:;-") for value in heading_variants}
    scanned: dict[int, list[dict[str, Any]]] = {}
    scan_batches: list[list[int]] = []
    warnings: list[str] = []
    heading_line: dict[str, Any] | None = None
    remaining = scan_limit
    batch_end = pages_total

    while remaining > 0 and batch_end >= 1:
        current_size = min(batch_size, remaining, batch_end)
        batch_start = batch_end - current_size + 1
        page_numbers = list(range(batch_start, batch_end + 1))
        scan_batches.append(page_numbers)
        result = ocr_batch(page_numbers)
        warnings.extend(str(value) for value in result.warnings if value)
        for page in result.pages:
            page_lines = []
            for line_index, raw in enumerate(page.lines or [], start=1):
                line = dict(raw)
                line.setdefault("page_number", page.page_index)
                line.setdefault("reading_order", line_index - 1)
                line["source_region"] = DECISION_TAIL
                line.setdefault(
                    "line_id",
                    f"p{page.page_index:03d}_l{line_index:04d}",
                )
                page_lines.append(line)
            scanned[page.page_index] = page_lines

        batch_lines = _ordered_lines(
            line
            for page_number in page_numbers
            for line in scanned.get(page_number, [])
        )
        heading_line = next(
            (
                line
                for line in reversed(batch_lines)
                if _is_decision_heading(str(line.get("text") or ""), normalized_headings)
            ),
            None,
        )
        if heading_line is not None:
            break
        remaining -= current_size
        batch_end = batch_start - 1

    all_lines = _ordered_lines(
        line
        for page_number in sorted(scanned)
        for line in scanned[page_number]
    )
    tail_lines: list[dict[str, Any]] = []
    if heading_line is not None:
        heading_key = _line_key(heading_line)
        start_index = next(
            index for index, line in enumerate(all_lines) if _line_key(line) == heading_key
        )
        tail_lines = all_lines[start_index:]
    else:
        warnings.append("decision_heading_not_found_within_scan_limit")

    return DecisionTailRecord(
        case_id=case_id,
        source_index=source_index,
        pdf_hash=pdf_hash,
        backend=backend,
        pages_total=pages_total,
        scanned_page_numbers=sorted(scanned),
        scan_batches=scan_batches,
        heading_found=heading_line is not None,
        heading_page=int(heading_line.get("page_number")) if heading_line else None,
        heading_line_id=str(heading_line.get("line_id")) if heading_line else None,
        heading_text=str(heading_line.get("text")) if heading_line else None,
        text="\n".join(
            str(line.get("text") or "") for line in tail_lines if line.get("text")
        ).strip(),
        lines=tail_lines,
        warnings=list(dict.fromkeys(warnings)),
        status="success" if heading_line is not None else "heading_not_found",
    )


def write_decision_tail_record(
    record: DecisionTailRecord,
    cache_dir: str | Path,
) -> Path:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{record.case_id}.json"
    path.write_text(
        json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def read_decision_tail_record(path: str | Path) -> DecisionTailRecord:
    return DecisionTailRecord.from_dict(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def read_decision_tail_cache_dir(
    cache_dir: str | Path,
) -> list[DecisionTailRecord]:
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return []
    return [
        read_decision_tail_record(path)
        for path in sorted(cache_dir.glob("case_*.json"))
    ]


def _is_decision_heading(text: str, normalized_headings: set[str]) -> bool:
    normalized = fold_text(text).strip(" .,:;-")
    return normalized in normalized_headings


def _ordered_lines(lines) -> list[dict[str, Any]]:
    return sorted(
        (dict(line) for line in lines),
        key=lambda line: (
            int(line.get("page_number") or 0),
            int(line.get("reading_order") or 0),
            str(line.get("line_id") or ""),
        ),
    )


def _line_key(line: dict[str, Any]) -> tuple[int, str, str]:
    return (
        int(line.get("page_number") or 0),
        str(line.get("line_id") or ""),
        str(line.get("text") or ""),
    )
