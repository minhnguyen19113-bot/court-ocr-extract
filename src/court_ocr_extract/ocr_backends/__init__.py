from __future__ import annotations

from court_ocr_extract.ocr_backends.base import OCRBackend
from court_ocr_extract.settings import PipelineSettings, get_settings


def get_ocr_backend(name: str | None = None, settings: PipelineSettings | None = None) -> OCRBackend:
    settings = settings or get_settings()
    backend_name = (name or settings.ocr_backend).strip().lower()
    if backend_name == "tesseract":
        from court_ocr_extract.ocr_backends.tesseract_ocr import TesseractOCRBackend

        return TesseractOCRBackend(settings)
    if backend_name == "google_vision":
        from court_ocr_extract.ocr_backends.google_vision_ocr import GoogleVisionOCRBackend

        return GoogleVisionOCRBackend(settings)
    if backend_name == "google_document_ai":
        from court_ocr_extract.ocr_backends.google_document_ai_ocr import GoogleDocumentAIOCRBackend

        return GoogleDocumentAIOCRBackend(settings)
    if backend_name == "openai_vision":
        from court_ocr_extract.ocr_backends.openai_vision_ocr import OpenAIVisionOCRBackend

        return OpenAIVisionOCRBackend(settings)
    if backend_name == "gemini_document":
        from court_ocr_extract.ocr_backends.gemini_document_ocr import GeminiDocumentOCRBackend

        return GeminiDocumentOCRBackend(settings)
    if backend_name in {"surya", "surya_optional"}:
        from court_ocr_extract.ocr_backends.surya_ocr import SuryaOCRBackend

        return SuryaOCRBackend(settings)
    raise ValueError(f"Unknown OCR backend: {backend_name}")


__all__ = ["OCRBackend", "get_ocr_backend"]
