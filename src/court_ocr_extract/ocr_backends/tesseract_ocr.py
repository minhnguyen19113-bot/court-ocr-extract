from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from court_ocr_extract.early_stop import find_marker_in_text
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRPage, OCRResult
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.settings import PipelineSettings


class TesseractOCRBackend:
    name = "tesseract"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        command = self._command()
        if not command:
            return OCRBackendStatus(self.name, False, "Tesseract binary was not found.")
        try:
            completed = subprocess.run(
                [command, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as exc:
            return OCRBackendStatus(self.name, False, f"Tesseract check failed: {exc}")
        if completed.returncode != 0:
            return OCRBackendStatus(self.name, False, "Tesseract returned a non-zero version check.")
        return OCRBackendStatus(self.name, True, "Tesseract binary is available.")

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
            temp_context = tempfile.TemporaryDirectory(prefix="court_ocr_tesseract_")
            work_dir = Path(temp_context.name)
        work_dir.mkdir(parents=True, exist_ok=True)

        pages: list[OCRPage] = []
        warnings: list[str] = []
        marker_found = False
        marker_page = None
        try:
            rendered_pages = render_pdf_pages(pdf_path, work_dir / "01_rendered", dpi=self.settings.ocr_dpi, max_pages=max_pages)
            for rendered in rendered_pages:
                text = self._ocr_image(rendered.image_path)
                marker = find_marker_in_text(text, stop_marker)
                page_text = marker.before_text if marker.found else text
                pages.append(
                    OCRPage(
                        page_index=rendered.page_number,
                        text=page_text,
                        image_path=str(rendered.image_path) if debug_visual else None,
                    )
                )
                if marker.found:
                    marker_found = True
                    marker_page = rendered.page_number
                    break
        finally:
            if temp_context is not None:
                temp_context.cleanup()

        combined_text = "\n\n".join(page.text for page in pages if page.text.strip())
        result_status = "success" if pages else "failed"
        if pages and not marker_found and len(pages) >= max_pages:
            result_status = "partial"
            warnings.append("Marker not found before max page limit.")
        return OCRResult(
            backend=self.name,
            status=result_status,
            pages_processed=len(pages),
            marker_found=marker_found,
            marker_page=marker_page,
            text=combined_text,
            pages=pages,
            warnings=warnings,
            timing={"total_seconds": time.perf_counter() - start},
        )

    def _ocr_image(self, image_path: Path) -> str:
        completed = subprocess.run(
            [self._command(), str(image_path), "stdout", "-l", self.settings.tesseract_lang],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if completed.returncode != 0:
            raise RuntimeError("Tesseract OCR failed for a page.")
        return completed.stdout

    def _command(self) -> str:
        if self.settings.tesseract_cmd:
            return self.settings.tesseract_cmd
        return shutil.which("tesseract") or ""
