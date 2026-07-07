from __future__ import annotations

from pathlib import Path
from typing import Any

from court_ocr_extract.evidence_viewer import evidence_status
from court_ocr_extract.excel_writer import EXCEL_HEADERS, rows_from_payload
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.visual_debug import escape, write_html


FIELD_MAP = {
    "TƯ CÁCH TỐ TỤNG": "procedural_role",
    "HỌ TÊN ĐƯƠNG SỰ": "full_name",
    "NĂM SINH": "birth_year",
    "CCCD": "id_number",
    "ĐỊA CHỈ": "address",
}


def write_extraction_preview(
    drafts: list[dict[str, Any]],
    records: list[OCRCacheRecord],
    output_dir: str | Path,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    record_by_case = {record.case_id: record for record in records}
    sections = ["<h1>Extraction Preview</h1>"]
    for draft in drafts:
        record = record_by_case.get(draft["case_id"])
        sections.append(_case_preview(draft, record))
    return write_html(output_dir / "index.html", "Extraction Preview", "\n".join(sections))


def _case_preview(draft: dict[str, Any], record: OCRCacheRecord | None) -> str:
    payload = draft.get("payload", {})
    rows = rows_from_payload(draft["case_id"], payload)
    left = _fields_table(rows)
    right = _evidence_panel(payload, record)
    return f"<section><h2>{escape(draft['case_id'])}</h2><div class=\"split\"><div>{left}</div><div>{right}</div></div></section>"


def _fields_table(rows: list[dict[str, Any]]) -> str:
    header = "".join(f"<th>{escape(name)}</th>" for name in [*EXCEL_HEADERS, "CONFIDENCE", "EVIDENCE STATUS"])
    body_rows = []
    for row_index, row in enumerate(rows):
        confidence = _row_confidence(row_index, rows)
        cells = "".join(f"<td>{escape(row.get(name))}</td>" for name in EXCEL_HEADERS)
        body_rows.append(f"<tr>{cells}<td>{escape(confidence)}</td><td>{escape(row.get('GHI CHÚ') or 'OK')}</td></tr>")
    return f"<table><tr>{header}</tr>{''.join(body_rows)}</table>"


def _evidence_panel(payload: dict[str, Any], record: OCRCacheRecord | None) -> str:
    chunks = ["<h3>Evidence</h3>"]
    for index, participant in enumerate(payload.get("participants", []), start=1):
        chunks.append(f"<h4>Participant {index}</h4><table>")
        for label, field in FIELD_MAP.items():
            evidence = (participant.get("evidence") or {}).get(field)
            chunks.append(
                "<tr>"
                f"<th>{escape(label)}</th>"
                f"<td><span class=\"badge\">{escape(evidence_status(participant, field))}</span><br>{escape(evidence)}</td>"
                "</tr>"
            )
        chunks.append("</table>")
    if record:
        snippet = (record.result.text or "")[:3000]
        chunks.append("<h3>OCR snippet around evidence</h3>")
        chunks.append(f"<pre>{escape(snippet)}</pre>")
    return "\n".join(chunks)


def _row_confidence(row_index: int, rows: list[dict[str, Any]]) -> str:
    return "see evidence"
