from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from court_ocr_extract.early_stop import find_marker_in_text
from court_ocr_extract.excel_writer import build_run_summary, write_excel
from court_ocr_extract.extraction_preview import write_extraction_preview
from court_ocr_extract.image_preprocess import make_before_after_compare, preprocess_image
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord, write_ocr_cache_record
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.qa import qa_excel
from court_ocr_extract.review_html import write_image_grid, write_marker_report, write_ocr_review
from court_ocr_extract.validation import validate_extraction_payload
from court_ocr_extract.visual_debug import escape, write_html


RUN_ID = "synthetic_smoke"
CASE_ID = "case_001_synthetic_smoke"
OCR_FIXTURE_TEXT = """TOA AN NHAN DAN - CONTRACT FIXTURE
Ho so thu ly so: 12/2026/TLST-HS ngay 03 thang 04 nam 2026.
Chu toa phien toa: Nguoi Chu Toa Fixture
Bi cao: Nguoi Tham Gia A, sinh nam 1990; CCCD so 012345678901; dia chi: Dia chi kiem tra contract.
NOI DUNG VU AN
Phan sau marker khong dung cho extraction smoke.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create safe synthetic debug outputs.")
    parser.add_argument("--output-root", default="outputs")
    parser.add_argument("--synthetic-root", default="data/synthetic/smoke")
    args = parser.parse_args(argv)
    result = run_smoke(output_root=Path(args.output_root), synthetic_root=Path(args.synthetic_root))
    print("Synthetic smoke finished")
    print(f"Manifest: {result['manifest_path']}")
    print(f"Debug index: {result['debug_index_path']}")
    print(f"Excel: {result['excel_path']}")
    print(f"QA report: {result['qa_report_path']}")


def run_smoke(*, output_root: Path, synthetic_root: Path) -> dict[str, str]:
    paths = _smoke_paths(output_root, synthetic_root)
    for directory in paths["directories"]:
        directory.mkdir(parents=True, exist_ok=True)

    steps: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        _create_synthetic_pdf(paths["synthetic_pdf"])
        steps.append(_step("synthetic_pdf", True, paths["synthetic_pdf"]))

        rendered = render_pdf_pages(
            paths["synthetic_pdf"],
            paths["render_dir"],
            dpi=150,
            page_numbers=[1],
        )
        rendered_image = rendered[0].image_path
        steps.append(_step("render", rendered_image.exists(), rendered_image))

        preprocessed = preprocess_image(rendered_image, paths["preprocess_after"])
        compare = make_before_after_compare(rendered_image, preprocessed, paths["preprocess_compare"])
        steps.append(_step("preprocess", preprocessed.exists() and compare.exists(), compare))

        paths["ocr_text"].write_text(OCR_FIXTURE_TEXT, encoding="utf-8")
        marker = find_marker_in_text(OCR_FIXTURE_TEXT, "NOI DUNG VU AN")
        paths["normalized_text"].write_text(marker.before_text, encoding="utf-8")
        steps.append(_step("fixture_ocr_text", paths["ocr_text"].exists(), paths["ocr_text"]))
        steps.append(_step("marker_normalization", marker.found, paths["normalized_text"]))

        record = OCRCacheRecord(
            case_id=CASE_ID,
            source_index=1,
            pdf_hash="synthetic-smoke",
            result=OCRResult(
                backend="synthetic_fixture_ocr",
                status="success",
                pages_processed=1,
                marker_found=marker.found,
                marker_page=1 if marker.found else None,
                text=marker.before_text,
                pages=[
                    OCRPage(
                        page_index=1,
                        text=marker.before_text,
                        image_path=str(rendered_image),
                    )
                ],
                warnings=[] if marker.found else ["Synthetic marker was not found."],
                timing={"total_seconds": 0.0},
            ),
        )
        ocr_cache_path = write_ocr_cache_record(record, paths["ocr_cache_dir"])
        steps.append(_step("ocr_cache", ocr_cache_path.exists(), ocr_cache_path))

        payload = validate_extraction_payload(_synthetic_extraction_payload())
        draft = {
            "case_id": CASE_ID,
            "source_index": 1,
            "ocr_backend": "synthetic_fixture_ocr",
            "extractor_backend": "synthetic_fixture_extractor",
            "marker_found": marker.found,
            "status": "success",
            "error": None,
            "payload": payload,
            "debug_run_id": RUN_ID,
        }
        _write_draft_artifacts([draft], paths)
        steps.append(_step("extraction_draft", paths["draft_jsonl"].exists(), paths["draft_jsonl"]))

        render_grid = write_image_grid(
            paths["render_grid_html"],
            title="Synthetic Render Review",
            cases=[{"case_id": CASE_ID, "images": [("rendered page", rendered_image)]}],
            base_dir=paths["debug_dir"],
        )
        preprocess_grid = write_image_grid(
            paths["preprocess_grid_html"],
            title="Synthetic Preprocess Review",
            cases=[{"case_id": CASE_ID, "images": [("before/after compare", compare)]}],
            base_dir=paths["debug_dir"],
        )
        ocr_review = write_ocr_review(paths["ocr_review_html"], [record], base_dir=paths["debug_dir"])
        marker_report = write_marker_report(paths["marker_report_html"], [record])
        extraction_preview = write_extraction_preview([draft], [record], paths["extraction_preview_dir"])
        steps.append(_step("debug_html", all(p.exists() for p in [render_grid, preprocess_grid, ocr_review, marker_report, extraction_preview]), paths["debug_dir"]))

        summary = build_run_summary([draft])
        summary["Debug visual run id"] = RUN_ID
        excel_path = write_excel([draft], paths["excel_path"], run_summary=summary)
        qa_summary = qa_excel(excel_path)
        paths["qa_report"].write_text(json.dumps(qa_summary, ensure_ascii=False, indent=2), encoding="utf-8")
        steps.append(_step("excel", excel_path.exists(), excel_path))
        steps.append(_step("qa_report", paths["qa_report"].exists(), paths["qa_report"]))

        index = _write_smoke_index(paths, qa_summary)
        steps.append(_step("debug_index", index.exists(), index))
    except Exception as exc:  # pragma: no cover - manifest is still useful for manual runs.
        errors.append(f"{type(exc).__name__}: {exc}")

    manifest = _manifest(paths, steps, errors)
    paths["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if errors or not all(step["pass"] for step in steps):
        raise SystemExit(1)
    return {
        "manifest_path": str(paths["manifest"]),
        "debug_index_path": str(paths["debug_index"]),
        "excel_path": str(paths["excel_path"]),
        "qa_report_path": str(paths["qa_report"]),
    }


def _smoke_paths(output_root: Path, synthetic_root: Path) -> dict[str, Any]:
    debug_dir = output_root / "debug_visual" / RUN_ID
    extraction_draft_dir = output_root / "extraction_draft" / RUN_ID
    qa_dir = output_root / "qa"
    return {
        "directories": [
            synthetic_root,
            debug_dir,
            debug_dir / CASE_ID / "01_rendered",
            debug_dir / CASE_ID / "02_preprocess",
            debug_dir / "extraction_preview",
            extraction_draft_dir,
            output_root / "excel",
            output_root / "ocr_cache" / RUN_ID,
            qa_dir,
        ],
        "synthetic_pdf": synthetic_root / "synthetic_smoke.pdf",
        "debug_dir": debug_dir,
        "render_dir": debug_dir / CASE_ID / "01_rendered",
        "preprocess_after": debug_dir / CASE_ID / "02_preprocess" / "page_001_after.png",
        "preprocess_compare": debug_dir / CASE_ID / "02_preprocess" / "page_001_compare.png",
        "render_grid_html": debug_dir / "render_review_grid.html",
        "preprocess_grid_html": debug_dir / "preprocess_review_grid.html",
        "ocr_review_html": debug_dir / "ocr_review.html",
        "marker_report_html": debug_dir / "marker_report.html",
        "extraction_preview_dir": debug_dir / "extraction_preview",
        "debug_index": debug_dir / "index.html",
        "manifest": debug_dir / "manifest.json",
        "ocr_text": output_root / "ocr_cache" / RUN_ID / "synthetic_ocr_text.txt",
        "normalized_text": output_root / "ocr_cache" / RUN_ID / "synthetic_normalized_text.txt",
        "ocr_cache_dir": output_root / "ocr_cache" / RUN_ID,
        "draft_jsonl": extraction_draft_dir / "draft_internal.jsonl",
        "draft_summary": extraction_draft_dir / "draft_summary.xlsx",
        "draft_json": extraction_draft_dir / f"{CASE_ID}.json",
        "excel_path": output_root / "excel" / "synthetic_smoke.xlsx",
        "qa_report": qa_dir / "synthetic_smoke_report.json",
    }


def _create_synthetic_pdf(path: Path) -> None:
    import fitz

    path.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    y = 72
    for line in OCR_FIXTURE_TEXT.splitlines():
        page.insert_text((72, y), line, fontsize=11)
        y += 24
    page.draw_circle((470, 170), 44, color=(1, 0, 0), fill=None, width=2)
    document.save(path)
    document.close()


def _synthetic_extraction_payload() -> dict[str, Any]:
    return {
        "case": {
            "case_type": "Hinh su",
            "filing_number": "12/2026/TLST-HS",
            "filing_date": "03/04/2026",
            "legal_relationship": "Kiem tra contract smoke",
            "presiding_judge": "Nguoi Chu Toa Fixture",
        },
        "participants": [
            {
                "procedural_role": "Bi cao",
                "full_name": "Nguoi Tham Gia A",
                "birth_year": "1990",
                "id_number": "012345678901",
                "address": "Dia chi kiem tra contract",
                "confidence": {
                    "procedural_role": 0.95,
                    "full_name": 0.95,
                    "birth_year": 0.9,
                    "id_number": 0.9,
                    "address": 0.85,
                },
                "evidence": {
                    "procedural_role": "Bi cao",
                    "full_name": "Nguoi Tham Gia A",
                    "birth_year": "sinh nam 1990",
                    "id_number": "CCCD so 012345678901",
                    "address": "dia chi: Dia chi kiem tra contract",
                },
                "warnings": [],
            }
        ],
        "document_warnings": [],
    }


def _write_draft_artifacts(drafts: list[dict[str, Any]], paths: dict[str, Any]) -> None:
    from openpyxl import Workbook

    paths["draft_json"].write_text(json.dumps(drafts[0], ensure_ascii=False, indent=2), encoding="utf-8")
    with paths["draft_jsonl"].open("w", encoding="utf-8") as handle:
        for draft in drafts:
            handle.write(json.dumps(draft, ensure_ascii=False) + "\n")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "DRAFT_SUMMARY"
    sheet.append(["CASE_ID", "STATUS", "OCR_BACKEND", "EXTRACTOR_BACKEND", "MARKER_FOUND", "PARTICIPANTS_COUNT"])
    for draft in drafts:
        sheet.append(
            [
                draft["case_id"],
                draft["status"],
                draft["ocr_backend"],
                draft["extractor_backend"],
                bool(draft["marker_found"]),
                len(draft["payload"].get("participants", [])),
            ]
        )
    workbook.save(paths["draft_summary"])


def _write_smoke_index(paths: dict[str, Any], qa_summary: dict[str, Any]) -> Path:
    debug_dir = paths["debug_dir"]
    links = [
        ("Render review", paths["render_grid_html"]),
        ("Preprocess review", paths["preprocess_grid_html"]),
        ("OCR review", paths["ocr_review_html"]),
        ("Marker report", paths["marker_report_html"]),
        ("Extraction preview", paths["extraction_preview_dir"] / "index.html"),
        ("Manifest JSON", paths["manifest"]),
    ]
    items = []
    for label, path in links:
        href = Path(path).resolve().relative_to(debug_dir.resolve()).as_posix()
        items.append(f'<li><a href="{escape(href)}">{escape(label)}</a></li>')
    body = (
        "<h1>Synthetic Smoke Debug</h1>"
        "<p>This output is generated from synthetic contract fixtures only. "
        "It does not prove real-data OCR/extraction quality.</p>"
        f"<h2>Links</h2><ul>{''.join(items)}</ul>"
        "<h2>External artifacts</h2>"
        "<table>"
        f"<tr><th>Excel</th><td>{escape(paths['excel_path'])}</td></tr>"
        f"<tr><th>QA report</th><td>{escape(paths['qa_report'])}</td></tr>"
        f"<tr><th>Draft JSONL</th><td>{escape(paths['draft_jsonl'])}</td></tr>"
        "</table>"
        "<h2>QA Summary</h2>"
        f"<pre>{escape(json.dumps(qa_summary, ensure_ascii=False, indent=2))}</pre>"
    )
    return write_html(paths["debug_index"], "Synthetic Smoke Debug", body)


def _manifest(paths: dict[str, Any], steps: list[dict[str, Any]], errors: list[str]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "real_data_accessed": False,
        "input_synthetic": str(paths["synthetic_pdf"]),
        "command": "python -m scripts.smoke_synthetic_debug",
        "modules_checked": [
            "pdf_render",
            "image_preprocess",
            "fixture_ocr",
            "marker_detection",
            "extraction_preview",
            "validation",
            "excel_writer",
            "qa",
            "debug_html",
        ],
        "steps": steps,
        "errors": errors,
        "output_paths": {
            "debug_index": str(paths["debug_index"]),
            "rendered_images": str(paths["render_dir"]),
            "preprocessed_images": str(paths["preprocess_after"].parent),
            "ocr_text": str(paths["ocr_text"]),
            "normalized_text": str(paths["normalized_text"]),
            "extraction_preview": str(paths["extraction_preview_dir"] / "index.html"),
            "draft_jsonl": str(paths["draft_jsonl"]),
            "validation_qa_report": str(paths["qa_report"]),
            "excel": str(paths["excel_path"]),
        },
    }


def _step(name: str, passed: bool, path: Path) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "path": str(path)}


if __name__ == "__main__":
    main()
