from __future__ import annotations

from pathlib import Path
from typing import Protocol

from court_ocr_extract.models import OcrDocument, OcrPage


class OcrAdapter(Protocol):
    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        ...


class BatchOcrAdapter(OcrAdapter, Protocol):
    def ocr_images(self, image_paths: list[str | Path], source_file: str | None = None) -> OcrDocument:
        ...
