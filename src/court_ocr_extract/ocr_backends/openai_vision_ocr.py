from __future__ import annotations

import base64
import json
import tempfile
import time
import urllib.request
from pathlib import Path

from court_ocr_extract.early_stop import find_marker_in_text
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRPage, OCRResult
from court_ocr_extract.pdf_render import render_pdf_pages
from court_ocr_extract.settings import PipelineSettings


class OpenAIVisionOCRBackend:
    name = "openai_vision"

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings

    def check_available(self) -> OCRBackendStatus:
        if not self.settings.enable_cloud_ocr:
            return OCRBackendStatus(self.name, False, "ENABLE_CLOUD_OCR must be true for OpenAI vision OCR.")
        if not self.settings.openai_api_key:
            return OCRBackendStatus(self.name, False, "OPENAI_API_KEY is required.")
        return OCRBackendStatus(self.name, True, "OpenAI vision OCR configuration is present.")

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int | None,
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
            temp_context = tempfile.TemporaryDirectory(prefix="court_ocr_openai_")
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
                marker = find_marker_in_text(text, stop_marker) if stop_marker else None
                pages.append(
                    OCRPage(
                        page_index=rendered.page_number,
                        text=marker.before_text if marker and marker.found else text,
                        image_path=str(rendered.image_path) if debug_visual else None,
                    )
                )
                if marker and marker.found:
                    marker_found = True
                    marker_page = rendered.page_number
                    break
        finally:
            if temp_context is not None:
                temp_context.cleanup()
        if stop_marker and max_pages is not None and pages and not marker_found:
            warnings.append("Marker not found before max page limit.")
        result_status = "success" if pages else "failed"
        if stop_marker and pages and not marker_found:
            result_status = "partial"
        return OCRResult(
            backend=self.name,
            status=result_status,
            pages_processed=len(pages),
            marker_found=marker_found,
            marker_page=marker_page,
            text="\n\n".join(page.text for page in pages if page.text.strip()),
            pages=pages,
            warnings=warnings,
            timing={"total_seconds": time.perf_counter() - start},
        )

    def _ocr_image(self, image_path: Path) -> str:
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "model": self.settings.openai_ocr_model,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "OCR this Vietnamese court document page. Return plain text only."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
                    ],
                }
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.openai_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["choices"][0]["message"]["content"])
