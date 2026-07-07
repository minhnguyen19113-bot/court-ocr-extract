from __future__ import annotations

from pathlib import Path
from typing import Any

from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.visual_debug import escape, rel_link, write_html


def write_run_index(run_dir: str | Path, links: dict[str, Path]) -> Path:
    run_dir = Path(run_dir)
    rows = []
    for label, path in links.items():
        rows.append(f'<li><a href="{escape(rel_link(path, run_dir))}">{escape(label)}</a></li>')
    body = "<h1>Visual QA</h1><ul>" + "\n".join(rows) + "</ul>"
    return write_html(run_dir / "index.html", "Visual QA", body)


def write_image_grid(
    output_path: str | Path,
    *,
    title: str,
    cases: list[dict[str, Any]],
    base_dir: str | Path,
) -> Path:
    base_dir = Path(base_dir)
    sections = [f"<h1>{escape(title)}</h1>"]
    for case in cases:
        images = []
        for label, image_path in case.get("images", []):
            image_path = Path(image_path)
            images.append(
                f"<div><h3>{escape(label)}</h3><img src=\"{escape(rel_link(image_path, base_dir))}\" alt=\"{escape(label)}\"></div>"
            )
        sections.append(
            f"<section><h2>{escape(case['case_id'])}</h2><div class=\"grid\">{''.join(images)}</div></section>"
        )
    return write_html(output_path, title, "\n".join(sections))


def write_ocr_review(output_path: str | Path, records: list[OCRCacheRecord], *, base_dir: str | Path) -> Path:
    base_dir = Path(base_dir)
    sections = ["<h1>OCR Review</h1>"]
    for record in records:
        page_chunks = []
        for page in record.result.pages:
            image_html = ""
            if page.image_path:
                image_path = Path(page.image_path)
                if image_path.exists():
                    image_html = f'<img src="{escape(rel_link(image_path, base_dir))}" alt="page {page.page_index}">'
            numbered_text = "\n".join(
                f"[{index:03d}] {line}" for index, line in enumerate((page.text or "").splitlines(), start=1)
            )
            page_chunks.append(
                f"<div class=\"split\"><div>{image_html}</div><pre>{escape(numbered_text)}</pre></div>"
            )
        sections.append(f"<section><h2>{escape(record.case_id)}</h2>{''.join(page_chunks)}</section>")
    return write_html(output_path, "OCR Review", "\n".join(sections))


def write_marker_report(output_path: str | Path, records: list[OCRCacheRecord]) -> Path:
    rows = [
        "<tr><th>CASE_ID</th><th>MARKER_FOUND</th><th>MARKER_PAGE</th><th>STATUS</th><th>WARNINGS</th></tr>"
    ]
    for record in records:
        rows.append(
            "<tr>"
            f"<td>{escape(record.case_id)}</td>"
            f"<td>{escape(record.result.marker_found)}</td>"
            f"<td>{escape(record.result.marker_page)}</td>"
            f"<td>{escape(record.result.status)}</td>"
            f"<td>{escape('; '.join(record.result.warnings))}</td>"
            "</tr>"
        )
    return write_html(output_path, "Marker Detection", "<h1>Marker Detection</h1><table>" + "\n".join(rows) + "</table>")
