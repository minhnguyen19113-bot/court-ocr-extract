from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import shutil
import tempfile
import time
from dataclasses import dataclass
from html import unescape
from importlib import metadata
from pathlib import Path
from typing import Any

from PIL import Image

from court_ocr_extract.bbox import draw_bbox_overlay
from court_ocr_extract.early_stop import find_marker_in_text
from court_ocr_extract.image_preprocess import preprocess_image
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRPage, OCRResult
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.review_html import write_ocr_review, write_run_index
from court_ocr_extract.settings import PipelineSettings


SUPPORTED_SURYA_OCR_VERSION = "0.20.0"


class SuryaRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class SuryaAPIDetection:
    kind: str
    version: str
    details: str


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
        installed_version = installed_surya_ocr_version()
        version_error = surya_version_guard_error(installed_version)
        if version_error:
            return OCRBackendStatus(self.name, False, version_error)
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
        detection = _detect_supported_surya_api()
        if detection.kind == "unsupported":
            return OCRBackendStatus(self.name, False, _unsupported_surya_api_message(detection))
        suffix = f" Version: {detection.version}." if detection.version else ""
        return OCRBackendStatus(
            self.name,
            True,
            f"Surya package is importable.{suffix} Supported version: {SUPPORTED_SURYA_OCR_VERSION}. "
            f"Adapter API: {detection.kind}.",
        )

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int | None,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
        preprocess_options: dict[str, Any] | None = None,
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
            image_paths = [page.image_path for page in rendered_pages]
            input_metadata_by_page: dict[int, dict[str, Any]] = {}
            result_metadata: dict[str, Any] = {"ocr_input_source": "rendered_original"}
            if preprocess_options is not None:
                image_paths, input_metadata_by_page, result_metadata = _preprocess_ocr_pages(
                    rendered_pages,
                    work_dir=work_dir,
                    options=preprocess_options,
                )
            result = self.ocr_images(
                image_paths,
                stop_marker=stop_marker,
                debug_visual=debug_visual,
                work_dir=work_dir,
                page_numbers=[page.page_number for page in rendered_pages],
                warn_if_marker_missing=bool(stop_marker and max_pages is not None),
                metadata=result_metadata,
                input_metadata_by_page=input_metadata_by_page,
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
        warn_if_marker_missing: bool = False,
        metadata: dict[str, Any] | None = None,
        input_metadata_by_page: dict[int, dict[str, Any]] | None = None,
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
        metadata = dict(metadata or {"ocr_input_source": "rendered_original"})
        input_metadata_by_page = input_metadata_by_page or {}
        warnings: list[str] = list(metadata.get("preprocess_warnings", []))
        marker_found = False
        marker_page = None

        for image_path, page_number, prediction in zip(image_paths, page_numbers, predictions):
            page_warnings: list[str] = []
            lines = normalize_surya_prediction(prediction, page_number=page_number, warnings=page_warnings)
            page_text = "\n".join(line["text"] for line in lines if line.get("text"))
            marker = find_marker_in_text(page_text, stop_marker) if stop_marker else None
            text_for_cache = marker.before_text if marker and marker.found else page_text
            if marker and marker.found:
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
                    input_metadata=input_metadata_by_page.get(page_number, metadata),
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
            if marker and marker.found:
                break

        combined_text = "\n\n".join(page.text for page in pages if page.text.strip())
        result_status = "success" if pages else "failed"
        if warn_if_marker_missing and pages and not marker_found and len(pages) >= len(image_paths):
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
            metadata=metadata,
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
            detection = _detect_supported_surya_api()
            if detection.kind == "unsupported":
                raise SuryaRuntimeError(_unsupported_surya_api_message(detection))
            try:
                return _run_detected_surya_api(
                    images,
                    self.settings.surya_language_list,
                    detection,
                )
            except SuryaRuntimeError:
                raise
            except Exception as exc:
                raise SuryaRuntimeError(
                    "Surya OCR runtime failed while using the supported adapter path. "
                    f"Detected {detection.details}. Original error: {exc}"
                ) from exc
        finally:
            for image in images:
                image.close()


def _preprocess_ocr_pages(rendered_pages, *, work_dir: Path, options: dict[str, Any]):
    normalized = {
        "deskew": str(options.get("deskew", "off")),
        "red_seal_removal": bool(options.get("red_seal_removal", True)),
        "red_removal_mode": str(options.get("red_removal_mode", "neutralize")),
        "text_enhance": str(options.get("text_enhance", "light")),
        "preprocess_profile": str(options.get("preprocess_profile", "conservative")),
    }
    preprocess_dir = Path(work_dir) / "preprocess"
    preprocess_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[Path] = []
    page_metadata: dict[int, dict[str, Any]] = {}
    aggregate_warnings: list[str] = []

    for page in rendered_pages:
        page_number = int(page.page_number)
        prefix = f"page_{page_number:03d}"
        original = preprocess_dir / f"{prefix}_original.png"
        red_mask = preprocess_dir / f"{prefix}_red_mask.png"
        protection = preprocess_dir / f"{prefix}_black_text_protection_mask.png"
        seal_removed = preprocess_dir / f"{prefix}_seal_removed.png"
        text_enhanced = preprocess_dir / f"{prefix}_text_enhanced.png"
        final = preprocess_dir / f"{prefix}_final_preprocessed.png"
        metadata_path = preprocess_dir / f"{prefix}_metadata.json"
        shutil.copy2(page.image_path, original)
        values: dict[str, Any] = {}
        try:
            preprocess_image(
                page.image_path,
                final,
                remove_red_seal=normalized["red_seal_removal"],
                intermediate_path=seal_removed,
                red_mask_path=red_mask,
                black_text_protection_path=protection,
                red_removal_mode=normalized["red_removal_mode"],
                text_enhanced_path=text_enhanced,
                text_enhance_mode=normalized["text_enhance"],
                deskew_mode=normalized["deskew"],
                preprocess_profile=normalized["preprocess_profile"],
                metadata=values,
            )
        except Exception as exc:
            shutil.copy2(page.image_path, final)
            values = {
                "warnings": [f"preprocess_failed_using_rendered_safe_copy:{type(exc).__name__}"],
                "fallback_source": "rendered_original_safe_copy",
            }
        values.update(
            {
                "page_number": page_number,
                "ocr_input_source": "preprocessed",
                **normalized,
                "original_path": str(original),
                "final_preprocessed_path": str(final),
            }
        )
        warnings = [str(item) for item in values.get("warnings", [])]
        aggregate_warnings.extend(f"page_{page_number:03d}:{warning}" for warning in warnings)
        metadata_path.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
        page_metadata[page_number] = values
        image_paths.append(final)

    result_metadata = {
        "ocr_input_source": "preprocessed",
        **normalized,
        "preprocess_warnings": _dedupe(aggregate_warnings),
    }
    return image_paths, page_metadata, result_metadata


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

    if records and all(record["reading_order"] is not None for record in records):
        records.sort(key=lambda record: int(record["reading_order"]))
    elif any(record["reading_order"] is None for record in records):
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
    input_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    original_path = artifacts_dir / f"page_{page_number:03d}_original.png"
    ocr_input_path = artifacts_dir / f"page_{page_number:03d}_ocr_input.png"
    bbox_path = artifacts_dir / f"page_{page_number:03d}_bbox.png"
    lines_path = artifacts_dir / f"page_{page_number:03d}_lines.json"
    text_path = artifacts_dir / f"page_{page_number:03d}_text.md"

    shutil.copy2(image_path, original_path)
    shutil.copy2(image_path, ocr_input_path)
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
        "ocr_input_image_path": str(ocr_input_path),
        "ocr_input_source": (input_metadata or {}).get("ocr_input_source", "rendered_original"),
        "ocr_input_metadata": dict(input_metadata or {}),
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
        "metadata": result.metadata,
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


def _run_detected_surya_api(
    images: list[Image.Image],
    languages: list[str],
    detection: SuryaAPIDetection,
) -> list[Any]:
    if detection.kind == "recognition_full_page":
        return _run_surya_recognition_full_page(images)
    if detection.kind == "recognition_with_detection":
        return _run_surya_recognition_with_detection(images, languages)
    if detection.kind == "legacy_run_ocr":
        return _run_surya_legacy(images, languages)
    raise SuryaRuntimeError(_unsupported_surya_api_message(detection))


def _run_surya_recognition_full_page(images: list[Image.Image]) -> list[Any]:
    from surya.recognition import RecognitionPredictor

    predictor = RecognitionPredictor()
    return list(predictor(images, full_page=True))


def _run_surya_recognition_with_detection(images: list[Image.Image], languages: list[str]) -> list[Any]:
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor

    recognition_predictor = RecognitionPredictor()
    detection_predictor = DetectionPredictor()
    lang_lists = [languages for _ in images]
    try:
        return list(recognition_predictor(images, lang_lists, detection_predictor))
    except TypeError as first_exc:
        try:
            return list(recognition_predictor(images, detection_predictor, lang_lists))
        except TypeError as second_exc:
            raise SuryaRuntimeError(
                "Surya package is installed but this adapter does not support the installed API. "
                "Detected recognition/detection API but could not call it. "
                f"First call error: {first_exc}; second call error: {second_exc}"
            ) from second_exc


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


def installed_surya_ocr_version() -> str:
    try:
        return metadata.version("surya-ocr")
    except metadata.PackageNotFoundError:
        return ""


def surya_version_guard_error(installed_version: str) -> str | None:
    reinstall = (
        'Reinstall with `.\\.venv\\Scripts\\python.exe -m pip uninstall -y surya-ocr` then '
        '`.\\.venv\\Scripts\\python.exe -m pip install -e ".[dev,ocr]"`. '
        "Verify with `.\\.venv\\Scripts\\python.exe -m pip show surya-ocr`."
    )
    if not installed_version:
        return (
            "surya-ocr is not installed. "
            f"Supported version: {SUPPORTED_SURYA_OCR_VERSION}. {reinstall} "
            f"Direct pinned install: `pip install surya-ocr=={SUPPORTED_SURYA_OCR_VERSION}`."
        )
    if installed_version == SUPPORTED_SURYA_OCR_VERSION:
        return None
    if _version_tuple(installed_version) >= (0, 21, 0):
        return (
            f"This project currently supports surya-ocr=={SUPPORTED_SURYA_OCR_VERSION} for the Surya adapter. "
            f"Detected surya-ocr {installed_version}, which requires Surya 2 inference backend / Docker. "
            "Please reinstall dependencies from the pinned project extras. "
            f"Installed version: {installed_version}. Supported version: {SUPPORTED_SURYA_OCR_VERSION}. {reinstall}"
        )
    return (
        f"Unsupported surya-ocr version. Installed version: {installed_version}. "
        f"Supported version: {SUPPORTED_SURYA_OCR_VERSION}. {reinstall}"
    )


def _version_tuple(value: str) -> tuple[int, int, int]:
    import re

    numbers = [int(item) for item in re.findall(r"\d+", value)[:3]]
    return tuple((numbers + [0, 0, 0])[:3])


def _surya_version() -> str:
    installed = installed_surya_ocr_version()
    if installed:
        return installed
    for package_name in ("surya-ocr", "surya"):
        try:
            return metadata.version(package_name)
        except metadata.PackageNotFoundError:
            continue
    module = importlib.import_module("surya")
    return str(getattr(module, "__version__", ""))


def _detect_supported_surya_api() -> SuryaAPIDetection:
    version = _surya_version()
    details: list[str] = [f"surya-ocr version {version or 'unknown'}"]

    try:
        recognition_module = importlib.import_module("surya.recognition")
        recognition_predictor = getattr(recognition_module, "RecognitionPredictor", None)
        if recognition_predictor is None:
            details.append("surya.recognition.RecognitionPredictor missing")
        else:
            signature = inspect.signature(recognition_predictor.__call__)
            details.append(f"RecognitionPredictor.__call__{signature}")
            parameters = signature.parameters
            if "full_page" in parameters:
                return SuryaAPIDetection("recognition_full_page", version, "; ".join(details))
            if _module_available("surya.detection") and _signature_may_accept_legacy_langs(signature):
                return SuryaAPIDetection("recognition_with_detection", version, "; ".join(details))
    except Exception as exc:
        details.append(f"surya.recognition inspection failed: {exc}")

    if _module_available("surya.ocr"):
        try:
            legacy_module = importlib.import_module("surya.ocr")
            if getattr(legacy_module, "run_ocr", None) is not None:
                details.append("surya.ocr.run_ocr present")
                return SuryaAPIDetection("legacy_run_ocr", version, "; ".join(details))
        except Exception as exc:
            details.append(f"surya.ocr inspection failed: {exc}")
    else:
        details.append("surya.ocr module missing")

    return SuryaAPIDetection("unsupported", version, "; ".join(details))


def _signature_may_accept_legacy_langs(signature: inspect.Signature) -> bool:
    parameter_names = [name for name in signature.parameters if name != "self"]
    return len(parameter_names) >= 3 or any(name in parameter_names for name in ("langs", "languages"))


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _unsupported_surya_api_message(detection: SuryaAPIDetection) -> str:
    return (
        "Surya package is installed but this adapter does not support the installed API. "
        f"Detected {detection.details}."
    )


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
