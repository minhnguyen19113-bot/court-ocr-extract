from __future__ import annotations

import importlib
import json
import shutil
import tempfile
import time
from html import unescape
from importlib import metadata
from pathlib import Path
from typing import Any

from PIL import Image

from court_ocr_extract.bbox import draw_bbox_overlay
from court_ocr_extract.early_stop import find_marker_in_text
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRPage, OCRResult
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.review_html import write_ocr_review, write_run_index
from court_ocr_extract.settings import PipelineSettings


class SuryaRuntimeError(RuntimeError):
    pass


class SuryaOCRBackend:
    name = "surya"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        if not self.settings.enable_surya_ocr:
            return OCRBackendStatus(
                self.name,
                False,
                "ENABLE_SURYA_OCR must be true; Surya is the target OCR backend.",
            )
        try:
            importlib.import_module("surya")
        except Exception as exc:
            return OCRBackendStatus(
                self.name,
                False,
                "Surya OCR package is not importable. Install with "
                '`pip install -e ".[ocr]"` or `pip install surya-ocr`. '
                f"Import error: {exc}",
            )
        version = _surya_version()
        suffix = f" Version: {version}." if version else ""
        return OCRBackendStatus(self.name, True, f"Surya package is importable.{suffix}")

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
    ) -> OCRResult:
        status = self.check_available()
        if not status.available:
            raise RuntimeError(status.reason)

        start = time.perf_counter()
        temp_context = None
        if work_dir is None:
            temp_context = tempfile.TemporaryDirectory(prefix="court_ocr_surya_")
            work_dir = Path(temp_context.name)
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            rendered_pages = render_pdf_pages(
                pdf_path,
                work_dir / "01_rendered",
                dpi=self.settings.ocr_dpi,
                max_pages=max_pages,
            )
            result = self.ocr_images(
                [page.image_path for page in rendered_pages],
                stop_marker=stop_marker,
                debug_visual=debug_visual,
                work_dir=work_dir,
                page_numbers=[page.page_number for page in rendered_pages],
            )
            result.timing["total_seconds"] = time.perf_counter() - start
            return result
        finally:
            if temp_context is not None:
                temp_context.cleanup()

    def ocr_images(
        self,
        image_paths: list[str | Path],
        *,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
        page_numbers: list[int] | None = None,
    ) -> OCRResult:
        status = self.check_available()
        if not status.available:
            raise RuntimeError(status.reason)

        start = time.perf_counter()
        image_paths = [Path(path) for path in image_paths]
        page_numbers = page_numbers or list(range(1, len(image_paths) + 1))
        predictions = self._run_surya_on_images(image_paths)

        artifacts_dir = None
        if debug_visual and work_dir is not None:
            artifacts_dir = Path(work_dir) / "ocr_surya"
            artifacts_dir.mkdir(parents=True, exist_ok=True)

        pages: list[OCRPage] = []
        warnings: list[str] = []
        marker_found = False
        marker_page = None

        for image_path, page_number, prediction in zip(image_paths, page_numbers, predictions):
            page_warnings: list[str] = []
            lines = normalize_surya_prediction(prediction, page_number=page_number, warnings=page_warnings)
            page_text = "\n".join(line["text"] for line in lines if line.get("text"))
            marker = find_marker_in_text(page_text, stop_marker)
            text_for_cache = marker.before_text if marker.found else page_text
            if marker.found:
                marker_found = True
                marker_page = page_number

            artifact_block: dict[str, Any] | None = None
            image_for_review: str | None = str(image_path) if debug_visual else None
            if artifacts_dir is not None:
                artifact_block = write_surya_page_artifacts(
                    artifacts_dir,
                    image_path=image_path,
                    page_number=page_number,
                    lines=lines,
                    page_text=text_for_cache,
                    warnings=page_warnings,
                )
                image_for_review = artifact_block.get("original_image_path")

            pages.append(
                OCRPage(
                    page_index=page_number,
                    text=text_for_cache,
                    lines=lines,
                    blocks=[artifact_block] if artifact_block else [],
                    image_path=image_for_review,
                )
            )
            warnings.extend(page_warnings)
            if marker.found:
                break

        combined_text = "\n\n".join(page.text for page in pages if page.text.strip())
        result_status = "success" if pages else "failed"
        if pages and not marker_found and len(pages) >= len(image_paths):
            result_status = "partial"
            warnings.append("Marker not found before max page limit.")

        result = OCRResult(
            backend=self.name,
            status=result_status,
            pages_processed=len(pages),
            marker_found=marker_found,
            marker_page=marker_page,
            text=combined_text,
            pages=pages,
            warnings=_dedupe(warnings),
            timing={"total_seconds": time.perf_counter() - start},
        )
        if artifacts_dir is not None:
            case_id = Path(work_dir).name if work_dir is not None else "surya_review"
            write_surya_run_artifacts(artifacts_dir, result, case_id=case_id)
        return result

    def _run_surya_on_images(self, image_paths: list[Path]) -> list[Any]:
        if not image_paths:
            return []
        images: list[Image.Image] = []
        try:
            images = [Image.open(path).convert("RGB") for path in image_paths]
            return _run_surya_modern(images, self.settings.surya_language_list)
        except Exception as modern_exc:
            try:
                return _run_surya_legacy(images, self.settings.surya_language_list)
            except Exception as legacy_exc:
                raise SuryaRuntimeError(
                    "Surya package is importable but the installed API is not wired for this adapter. "
                    "Update `SuryaOCRBackend` for the installed Surya version. "
                    f"Modern API error: {modern_exc}; legacy API error: {legacy_exc}"
                ) from legacy_exc
        finally:
            for image in images:
                image.close()


def normalize_surya_prediction(
    prediction: Any,
    *,
    page_number: int,
    warnings: list[str] | None = None,
) -> list[dict[str, Any]]:
    warnings = warnings if warnings is not None else []
    raw_items = _get_ocr_items(prediction)
    records: list[dict[str, Any]] = []
    for item in raw_items:
        text = _get_text(item)
        if not text:
            continue
        bbox = _bbox_from_item(item)
        item_warnings = []
        if bbox is None:
            item_warnings.append("missing_bbox")
        records.append(
            {
                "line_id": "",
                "page_number": page_number,
                "text": text,
                "bbox": bbox,
                "confidence": _confidence_from_item(item),
                "reading_order": _reading_order_from_item(item),
                "warnings": item_warnings,
            }
        )

    if any(record["reading_order"] is None for record in records):
        if all(record.get("bbox") for record in records):
            records.sort(key=lambda record: (float(record["bbox"][1]), float(record["bbox"][0])))
        warnings.append("reading_order_fallback_used")

    for index, record in enumerate(records, start=1):
        record["line_id"] = f"p{page_number:03d}_l{index:04d}"
        record["reading_order"] = index
    return records


def write_surya_page_artifacts(
    artifacts_dir: str | Path,
    *,
    image_path: str | Path,
    page_number: int,
    lines: list[dict[str, Any]],
    page_text: str,
    warnings: list[str],
) -> dict[str, Any]:
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    original_path = artifacts_dir / f"page_{page_number:03d}_original.png"
    bbox_path = artifacts_dir / f"page_{page_number:03d}_bbox.png"
    lines_path = artifacts_dir / f"page_{page_number:03d}_lines.json"
    text_path = artifacts_dir / f"page_{page_number:03d}_text.md"

    shutil.copy2(image_path, original_path)
    if any(line.get("bbox") for line in lines):
        draw_bbox_overlay(original_path, lines, bbox_path, color="red")
    else:
        shutil.copy2(original_path, bbox_path)
        warnings.append("no_bbox_for_overlay")

    lines_path.write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")
    text_path.write_text(page_text, encoding="utf-8")
    return {
        "type": "surya_artifacts",
        "original_image_path": str(original_path),
        "bbox_image_path": str(bbox_path),
        "lines_json_path": str(lines_path),
        "text_markdown_path": str(text_path),
        "warnings": list(warnings),
    }


def write_surya_run_artifacts(
    artifacts_dir: str | Path,
    result: OCRResult,
    *,
    case_id: str = "surya_review",
) -> dict[str, Path]:
    artifacts_dir = Path(artifacts_dir)
    combined_text = artifacts_dir / "combined_text.md"
    manifest = artifacts_dir / "manifest.json"
    review = artifacts_dir / "ocr_review.html"
    index = artifacts_dir / "index.html"
    combined_text.write_text(result.text, encoding="utf-8")
    payload = {
        "backend": result.backend,
        "status": result.status,
        "pages_processed": result.pages_processed,
        "marker_found": result.marker_found,
        "marker_page": result.marker_page,
        "total_lines": sum(len(page.lines) for page in result.pages),
        "warnings": result.warnings,
        "pages": [
            {
                "page_index": page.page_index,
                "lines_count": len(page.lines),
                "artifacts": page.blocks[0] if page.blocks else {},
            }
            for page in result.pages
        ],
    }
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_ocr_review(review, [_record_for_review(result, case_id=case_id)], base_dir=artifacts_dir)
    write_run_index(artifacts_dir, {"Surya OCR review": review, "Manifest": manifest})
    return {"combined_text": combined_text, "manifest": manifest, "review": review, "index": index}


def _record_for_review(result: OCRResult, *, case_id: str):
    from court_ocr_extract.ocr_cache import OCRCacheRecord

    return OCRCacheRecord(case_id=case_id, source_index=0, pdf_hash=None, result=result)


def _run_surya_modern(images: list[Image.Image], languages: list[str]) -> list[Any]:
    try:
        from surya.inference import SuryaInferenceManager
        from surya.recognition import RecognitionPredictor
    except Exception as exc:
        raise SuryaRuntimeError(f"Modern Surya API import failed: {exc}") from exc

    manager = SuryaInferenceManager()
    predictor = RecognitionPredictor(manager)
    try:
        return list(predictor(images))
    except TypeError:
        return list(predictor(images, langs=[languages for _ in images]))


def _run_surya_legacy(images: list[Image.Image], languages: list[str]) -> list[Any]:
    from surya.model.detection.model import load_model as load_det_model
    from surya.model.detection.model import load_processor as load_det_processor
    from surya.model.recognition.model import load_model as load_rec_model
    from surya.model.recognition.processor import load_processor as load_rec_processor
    from surya.ocr import run_ocr

    return list(
        run_ocr(
            images,
            [languages for _ in images],
            load_det_model(),
            load_det_processor(),
            load_rec_model(),
            load_rec_processor(),
        )
    )


def _surya_version() -> str:
    for package_name in ("surya-ocr", "surya"):
        try:
            return metadata.version(package_name)
        except metadata.PackageNotFoundError:
            continue
    module = importlib.import_module("surya")
    return str(getattr(module, "__version__", ""))


def _get_ocr_items(prediction: Any) -> list[Any]:
    if isinstance(prediction, dict):
        return prediction.get("text_lines") or prediction.get("lines") or prediction.get("blocks") or []
    return (
        getattr(prediction, "text_lines", None)
        or getattr(prediction, "lines", None)
        or getattr(prediction, "blocks", None)
        or []
    )


def _get_attr(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _get_text(item: Any) -> str:
    text = _get_attr(item, "text", None)
    if text:
        return str(text).strip()
    html = _get_attr(item, "html", None)
    if html:
        return _html_to_text(str(html))
    return ""


def _bbox_from_item(item: Any) -> list[float] | None:
    bbox = _get_attr(item, "bbox", None) or _get_attr(item, "box", None)
    polygon = _get_attr(item, "polygon", None)
    if bbox is None and polygon:
        try:
            xs = [float(point[0]) for point in polygon]
            ys = [float(point[1]) for point in polygon]
            bbox = [min(xs), min(ys), max(xs), max(ys)]
        except (TypeError, ValueError, IndexError):
            bbox = None
    if not bbox or len(bbox) != 4:
        return None
    try:
        return [float(value) for value in bbox]
    except (TypeError, ValueError):
        return None


def _confidence_from_item(item: Any) -> float | None:
    confidence = _get_attr(item, "confidence", None)
    if confidence is None:
        confidence = _get_attr(item, "score", None)
    if confidence is None:
        return None
    try:
        return float(confidence)
    except (TypeError, ValueError):
        return None


def _reading_order_from_item(item: Any) -> int | None:
    for name in ("reading_order", "order", "position"):
        value = _get_attr(item, name, None)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _html_to_text(value: str) -> str:
    import re

    value = re.sub(r"</(p|div|li|tr|br)>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
