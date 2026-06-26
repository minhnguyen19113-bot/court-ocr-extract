from __future__ import annotations

import re
import time
from html import unescape
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from court_ocr_extract.models import OcrDocument, OcrLine, OcrPage, model_to_dict


class SuryaUnavailableError(RuntimeError):
    pass


class OcrEngine(Protocol):
    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        ...


class MockOcrEngine:
    def __init__(self, page_texts: dict[int, str] | None = None) -> None:
        self.page_texts = page_texts or {}

    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        image_path = Path(image_path)
        start = time.perf_counter()
        text = self.page_texts.get(page_number)
        if text is None:
            sidecar = image_path.with_suffix(".txt")
            if sidecar.exists():
                text = sidecar.read_text(encoding="utf-8")
            else:
                text = _default_mock_text(page_number)

        width, height = _image_size(image_path)
        lines = []
        for index, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            top = 40 + index * 34
            lines.append(
                OcrLine(
                    text=line.strip(),
                    page_number=page_number,
                    bbox=[40.0, float(top), 1200.0, float(top + 28)],
                    confidence=0.99,
                )
            )
        return OcrPage(
            page_number=page_number,
            width=width,
            height=height,
            lines=lines,
            text=text,
            ocr_time=time.perf_counter() - start,
            processed_image_path=str(image_path),
        )


class SuryaOcrEngine:
    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = languages or ["vi"]
        self._models: tuple[Any, ...] | None = None

    def _load_models(self) -> tuple[Any, ...]:
        if self._models is not None:
            return self._models

        try:
            from surya.inference import SuryaInferenceManager
            from surya.recognition import RecognitionPredictor

            manager = SuryaInferenceManager()
            recognition_predictor = RecognitionPredictor(manager)
            self._models = ("v2", recognition_predictor)
            return self._models
        except Exception:
            pass

        try:
            from surya.model.detection.model import load_model as load_det_model
            from surya.model.detection.model import load_processor as load_det_processor
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.model.recognition.processor import load_processor as load_rec_processor
            from surya.ocr import run_ocr
        except Exception as exc:
            raise SuryaUnavailableError(
                "Surya OCR chưa sẵn sàng. Cài dependencies GPU hoặc bật ENABLE_MOCK_OCR=true để test."
            ) from exc

        self._models = (
            "v1",
            run_ocr,
            load_det_model(),
            load_det_processor(),
            load_rec_model(),
            load_rec_processor(),
        )
        return self._models

    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        image_path = Path(image_path)
        model_bundle = self._load_models()
        start = time.perf_counter()
        image = Image.open(image_path).convert("RGB")
        width, height = image.size
        try:
            try:
                if model_bundle[0] == "v2":
                    prediction = model_bundle[1]([image])[0]
                else:
                    _, run_ocr, det_model, det_processor, rec_model, rec_processor = model_bundle
                    prediction = run_ocr(
                        [image],
                        [self.languages],
                        det_model,
                        det_processor,
                        rec_model,
                        rec_processor,
                    )[0]
            except Exception as exc:
                raise SuryaUnavailableError(_surya_runtime_help(exc)) from exc
        finally:
            image.close()

        lines = [
            _line_from_surya(item, page_number=page_number)
            for item in _get_ocr_items(prediction)
            if _get_text(item)
        ]
        return OcrPage(
            page_number=page_number,
            width=width,
            height=height,
            lines=lines,
            text=None,
            ocr_time=time.perf_counter() - start,
            processed_image_path=str(image_path),
        )

    def ocr_images(self, image_paths: list[str | Path], source_file: str | None = None) -> OcrDocument:
        pages = [self.ocr_page(image_path, index) for index, image_path in enumerate(image_paths, start=1)]
        return OcrDocument(source_file=source_file, pages=pages, pages_ocr=len(pages))


def save_ocr_document(document: OcrDocument, output_path: str | Path) -> Path:
    from court_ocr_extract.file_utils import write_json

    return write_json(Path(output_path), model_to_dict(document))


def load_ocr_document(path: str | Path) -> OcrDocument:
    import json

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return OcrDocument(**payload)


def _get_ocr_items(prediction: Any) -> list[Any]:
    if isinstance(prediction, dict):
        return prediction.get("blocks") or prediction.get("text_lines") or prediction.get("lines") or []
    return (
        getattr(prediction, "blocks", None)
        or getattr(prediction, "text_lines", None)
        or getattr(prediction, "lines", None)
        or []
    )


def _get_attr(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _line_from_surya(item: Any, page_number: int) -> OcrLine:
    text = _get_text(item)
    confidence = _get_attr(item, "confidence", None)
    bbox = _get_attr(item, "bbox", None)
    polygon = _get_attr(item, "polygon", None)
    if bbox is None and polygon:
        xs = [point[0] for point in polygon]
        ys = [point[1] for point in polygon]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    return OcrLine(
        text=text,
        bbox=[float(value) for value in (bbox or [])],
        confidence=float(confidence) if confidence is not None else None,
        page_number=page_number,
    )


def _get_text(item: Any) -> str:
    text = _get_attr(item, "text", None)
    if text:
        return str(text).strip()
    html = _get_attr(item, "html", None)
    if html:
        return _html_to_text(str(html))
    return ""


def _html_to_text(value: str) -> str:
    value = re.sub(r"</(p|div|li|tr|br)>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def _image_size(path: Path) -> tuple[int | None, int | None]:
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None, None


def _default_mock_text(page_number: int) -> str:
    if page_number == 1:
        return (
            "TÒA ÁN NHÂN DÂN HUYỆN A\n"
            "BẢN ÁN HÌNH SỰ SƠ THẨM\n"
            "Vụ án hình sự thụ lý số: 12/2025/TLST-HS ngày 03 tháng 04 năm 2025.\n"
            "Thẩm phán - Chủ tọa phiên tòa: Người Chủ Tọa\n"
            "Bị cáo: Người Tham Gia A, sinh năm 1990; CCCD số 012345678901; nơi cư trú: xã B, huyện C.\n"
        )
    if page_number == 2:
        return "NỘI DUNG VỤ ÁN\nPhần này không dùng để bóc tách."
    return ""


def _surya_runtime_help(exc: Exception) -> str:
    message = str(exc)
    if "llama-server binary not found" in message or "LLAMA_CPP_BINARY" in message:
        return (
            "Surya OCR cần `llama-server` nhưng máy local chưa tìm thấy binary. "
            "Cách nhanh để test pipeline: thêm `--mock-ocr --mock-local-llm`. "
            "Để OCR thật local, cài llama.cpp và set LLAMA_CPP_BINARY tới "
            "`llama-server.exe`, hoặc chuyển sang remote GPU worker."
        )
    return (
        "Surya OCR lỗi khi nhận dạng trang. Có thể dùng `--mock-ocr` để test pipeline, "
        "hoặc kiểm tra lại cài đặt Surya/GPU/llama.cpp. Chi tiết kỹ thuật: "
        f"{message}"
    )


SuryaOcrAdapter = SuryaOcrEngine
