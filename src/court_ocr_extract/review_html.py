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


def write_preprocess_review(
    output_path: str | Path,
    *,
    cases: list[dict[str, Any]],
    base_dir: str | Path,
) -> Path:
    base_dir = Path(base_dir)
    sections = ["<h1>Preprocess Safety Review</h1>"]
    metadata_fields = [
        "page_number",
        "preprocess_profile",
        "red_pixels_ratio",
        "red_mask_components",
        "red_mask_method",
        "red_removal_mode",
        "red_seal_removed",
        "red_removed_ratio",
        "red_residual_ratio_estimate",
        "dark_text_overlap_ratio",
        "text_enhance_mode",
        "foreground_before_enhance",
        "foreground_after_enhance",
        "dark_pixel_ratio_before",
        "dark_pixel_ratio_after",
        "deskew_mode",
        "detected_angle",
        "deskew_applied",
        "deskew_confidence",
        "deskew_reason",
        "foreground_before",
        "foreground_after",
        "fallback_source",
        "warnings",
    ]
    for case in cases:
        page_sections = []
        for page in case.get("pages", []):
            images = []
            for label, image_path in page.get("images", []):
                image_path = Path(image_path)
                if image_path.exists():
                    images.append(
                        f'<div><h4>{escape(label)}</h4><img src="{escape(rel_link(image_path, base_dir))}" '
                        f'alt="{escape(label)}"></div>'
                    )
            metadata = page.get("metadata", {})
            rows = []
            for field in metadata_fields:
                value = metadata.get(field)
                if isinstance(value, list):
                    value = "; ".join(str(item) for item in value)
                rows.append(f"<tr><th>{escape(field)}</th><td>{escape(value)}</td></tr>")
            page_sections.append(
                "<section>"
                f"<h3>Page {escape(metadata.get('page_number'))}</h3>"
                f"<div class=\"grid\">{''.join(images)}</div>"
                f"<table>{''.join(rows)}</table>"
                "</section>"
            )
        sections.append(f"<section><h2>{escape(case['case_id'])}</h2>{''.join(page_sections)}</section>")
    return write_html(output_path, "Preprocess Safety Review", "\n".join(sections))


def write_ocr_review(output_path: str | Path, records: list[OCRCacheRecord], *, base_dir: str | Path) -> Path:
    base_dir = Path(base_dir)
    sections = ["<h1>OCR Review</h1>"]
    for record in records:
        page_chunks = []
        for page in record.result.pages:
            artifact = _artifact_block(page.blocks)
            image_html = ""
            if page.image_path:
                image_path = Path(page.image_path)
                if image_path.exists():
                    image_html = f'<img src="{escape(rel_link(image_path, base_dir))}" alt="page {page.page_index}">'
            overlay_html = ""
            if artifact and artifact.get("bbox_image_path"):
                overlay_path = Path(artifact["bbox_image_path"])
                if overlay_path.exists():
                    overlay_html = (
                        f'<img src="{escape(rel_link(overlay_path, base_dir))}" '
                        f'alt="page {page.page_index} bbox overlay">'
                    )
            links = []
            if artifact:
                for label, key in [("text", "text_markdown_path"), ("lines json", "lines_json_path")]:
                    path_value = artifact.get(key)
                    if path_value and Path(path_value).exists():
                        links.append(f'<a href="{escape(rel_link(Path(path_value), base_dir))}">{escape(label)}</a>')
            line_table = _line_table(page.lines)
            warnings = []
            warnings.extend(record.result.warnings)
            if artifact:
                warnings.extend(str(item) for item in artifact.get("warnings", []))
            numbered_text = "\n".join(
                f"[{index:03d}] {line}" for index, line in enumerate((page.text or "").splitlines(), start=1)
            )
            page_chunks.append(
                "<section>"
                f"<h3>Page {escape(page.page_index)}</h3>"
                f"<p>{' | '.join(links)}</p>"
                f"<p>{escape('; '.join(_dedupe(warnings)))}</p>"
                f"<div class=\"split\"><div><h4>Original</h4>{image_html}</div>"
                f"<div><h4>Bbox overlay</h4>{overlay_html}</div></div>"
                f"<h4>Lines</h4>{line_table}"
                f"<h4>Page text</h4><pre>{escape(numbered_text)}</pre>"
                "</section>"
            )
        sections.append(f"<section><h2>{escape(record.case_id)}</h2>{''.join(page_chunks)}</section>")
    return write_html(output_path, "OCR Review", "\n".join(sections))


def _artifact_block(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for block in blocks or []:
        if block.get("type") == "surya_artifacts":
            return block
    return None


def _line_table(lines: list[dict[str, Any]]) -> str:
    rows = [
        "<tr><th>line_id</th><th>text</th><th>bbox</th><th>confidence</th><th>warning</th></tr>"
    ]
    for line in lines or []:
        rows.append(
            "<tr>"
            f"<td>{escape(line.get('line_id'))}</td>"
            f"<td>{escape(line.get('text'))}</td>"
            f"<td>{escape(line.get('bbox'))}</td>"
            f"<td>{escape(line.get('confidence'))}</td>"
            f"<td>{escape('; '.join(str(item) for item in line.get('warnings', [])))}</td>"
            "</tr>"
        )
    return "<table>" + "\n".join(rows) + "</table>"


def _dedupe(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


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
