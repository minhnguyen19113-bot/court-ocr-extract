from __future__ import annotations

from typing import Protocol

from court_ocr_extract.models import ExtractorOutput


class InformationExtractor(Protocol):
    method: str

    def extract(self, text: str) -> ExtractorOutput:
        ...
