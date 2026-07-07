from __future__ import annotations

import base64
import json
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from court_ocr_extract.early_stop import find_marker_in_text
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRPage, OCRResult
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.settings import PipelineSettings


class GeminiDocumentOCRBackend:
    name = "gemini_document"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        if not self.settings.enable_cloud_ocr:
            return OCRBackendStatus(self.name, False, "ENABLE_CLOUD_OCR must be true for Gemini OCR.")
        if not self.settings.google_api_key:
            return OCRBackendStatus(self.name, False, "GOOGLE_API_KEY is required.")
        return OCRBackendStatus(self.name, True, "Gemini OCR configuration is present.")

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
            temp_context = tempfile.TemporaryDirectory(prefix="court_ocr_gemini_")
            work_dir = Path(temp_context.name)
        work_dir.mkdir(parents=True, exist_ok=True)
        pages: list[OCRPage] = []
        marker_found = False
        marker_page = None
        warnings: list[str] = []
        try:
            rendered_pages = render_pdf_pages(pdf_path, work_dir / "01_rendered", dpi=self.settings.ocr_dpi, max_pages=max_pages)
            for rendered in rendered_pages:
                text = self._ocr_image(rendered.image_path)
                marker = find_marker_in_text(text, stop_marker)
                pages.append(
                    OCRPage(
                        page_index=rendered.page_number,
                        text=marker.before_text if marker.found else text,
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
        if pages and not marker_found:
            warnings.append("Marker not found before max page limit.")
        return OCRResult(
            backend=self.name,
            status="success" if pages and marker_found else "partial" if pages else "failed",
            pages_processed=len(pages),
            marker_found=marker_found,
            marker_page=marker_page,
            text="\n\n".join(page.text for page in pages if page.text.strip()),
            pages=pages,
            warnings=warnings,
            timing={"total_seconds": time.perf_counter() - start},
        )

    def _ocr_image(self, image_path: Path) -> str:
        model = urllib.parse.quote(self.settings.gemini_ocr_model, safe="")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.settings.google_api_key}"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": "OCR this Vietnamese court document page. Return plain text only."},
                        {"inline_data": {"mime_type": "image/png", "data": encoded}},
                    ],
                }
            ]
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["candidates"][0]["content"]["parts"][0]["text"])
