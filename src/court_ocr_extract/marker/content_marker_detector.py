from __future__ import annotations

from court_ocr_extract.postprocess.section_splitter import (
    MARKER_NOI_DUNG,
    MarkerMatch,
    SectionSplit,
    find_marker,
    split_before_marker,
)


def detect_content_marker(
    text: str,
    *,
    marker: str = MARKER_NOI_DUNG,
    threshold: float = 82,
) -> MarkerMatch:
    return find_marker(text, threshold=threshold, marker=marker)


def split_before_content_marker(
    text: str,
    *,
    marker: str = MARKER_NOI_DUNG,
    threshold: float = 82,
) -> SectionSplit:
    return split_before_marker(text, threshold=threshold, marker=marker)
