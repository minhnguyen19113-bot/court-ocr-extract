from __future__ import annotations

from pathlib import Path

from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRResult
from court_ocr_extract.settings import PipelineSettings


class SuryaOCRBackend:
    name = "surya"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        if not self.settings.enable_surya_ocr:
            return OCRBackendStatus(self.name, False, "ENABLE_SURYA_OCR must be true; Surya is the target OCR backend.")
        try:
            import surya  # noqa: F401
        except Exception as exc:
            return OCRBackendStatus(self.name, False, f"Surya import failed: {exc}")
        return OCRBackendStatus(self.name, True, "Surya package is importable.")

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
    ) -> OCRResult:
        raise RuntimeError("Surya OCR runtime wiring is incomplete; finish Surya integration in a later phase.")
