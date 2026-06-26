from __future__ import annotations

from court_ocr_extract.postprocess.normalize_text import normalize_ocr_text
from court_ocr_extract.postprocess.section_splitter import (
    MARKER_NOI_DUNG,
    MarkerMatch,
    find_marker as find_noi_dung_marker,
    split_before_marker,
)


def text_before_noi_dung(text: str) -> tuple[str, MarkerMatch]:
    split = split_before_marker(text)
    return split.before_text, split.marker


__all__ = [
    "MARKER_NOI_DUNG",
    "MarkerMatch",
    "find_noi_dung_marker",
    "normalize_ocr_text",
    "text_before_noi_dung",
]
