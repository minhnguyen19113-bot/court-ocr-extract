from __future__ import annotations

from pathlib import Path

from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRResult
from court_ocr_extract.settings import PipelineSettings


class GoogleDocumentAIOCRBackend:
    name = "google_document_ai"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        missing = []
        if not self.settings.enable_cloud_ocr:
            missing.append("ENABLE_CLOUD_OCR=true")
        if not self.settings.google_application_credentials:
            missing.append("GOOGLE_APPLICATION_CREDENTIALS")
        if not self.settings.google_cloud_project:
            missing.append("GOOGLE_CLOUD_PROJECT")
        if not self.settings.google_document_ai_processor_id:
            missing.append("GOOGLE_DOCUMENT_AI_PROCESSOR_ID")
        if missing:
            return OCRBackendStatus(self.name, False, "Missing: " + ", ".join(missing))
        return OCRBackendStatus(self.name, True, "Google Document AI configuration is present.")

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
    ) -> OCRResult:
        raise RuntimeError("Google Document AI OCR adapter requires installing the Google SDK before use.")
