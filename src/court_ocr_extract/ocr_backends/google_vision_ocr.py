from __future__ import annotations

from pathlib import Path

from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRResult
from court_ocr_extract.settings import PipelineSettings


class GoogleVisionOCRBackend:
    name = "google_vision"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        if not self.settings.enable_cloud_ocr:
            return OCRBackendStatus(self.name, False, "ENABLE_CLOUD_OCR must be true for Google Vision OCR.")
        if not self.settings.google_application_credentials:
            return OCRBackendStatus(self.name, False, "GOOGLE_APPLICATION_CREDENTIALS is required.")
        return OCRBackendStatus(self.name, True, "Google Vision OCR configuration is present.")

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
    ) -> OCRResult:
        raise RuntimeError("Google Vision OCR adapter is configured but the SDK call is not installed in this minimal build.")
