from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from court_ocr_extract.review_sampling import ReviewCandidate


HEADERS = [
    "CASE_ID",
    "SOURCE_INDEX",
    "SELECT_REASON",
    "OCR_BACKEND",
    "EXTRACTOR_BACKEND",
    "MARKER_FOUND",
    "STATUS",
    "WARNINGS_COUNT",
    "DEBUG_LINK",
]


def write_review_manifest(
    candidates: list[ReviewCandidate],
    output_path: str | Path,
    *,
    ocr_backend: str,
    extractor_backend: str = "",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "REVIEW_SAMPLE"
    sheet.append(HEADERS)
    for item in candidates:
        sheet.append(
            [
                item.case_id,
                item.source_index,
                item.metadata.get("select_reason", ""),
                ocr_backend,
                extractor_backend,
                bool(item.marker_found),
                item.status,
                item.warnings_count,
                item.metadata.get("debug_link", ""),
            ]
        )
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = min(max(len(str(column[0].value)) + 4, 14), 42)
    workbook.save(output_path)
    return output_path
