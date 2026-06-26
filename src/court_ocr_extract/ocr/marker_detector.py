from __future__ import annotations

from court_ocr_extract.models import OcrLine, OcrPage
from court_ocr_extract.postprocess.section_splitter import MarkerMatch, find_marker


def detect_marker_in_page(
    page: OcrPage,
    marker: str,
    threshold: float = 82,
) -> MarkerMatch:
    return find_marker(page.page_text, threshold=threshold, marker=marker)


def trim_page_above_marker(page: OcrPage, marker_match: MarkerMatch) -> OcrPage:
    """Return a page containing only OCR lines before the marker span.

    If the marker starts in the middle of a line, the prefix before the marker is
    retained with the original bbox as a best-effort line-level approximation.
    """
    if not marker_match.found or marker_match.start is None:
        return page

    lines: list[OcrLine] = []
    offset = 0
    for line in page.lines:
        raw = line.text or ""
        line_start = offset
        line_end = offset + len(raw)
        next_offset = line_end + 1

        if line_end <= marker_match.start:
            lines.append(line)
        elif line_start < marker_match.start < line_end:
            prefix = raw[: marker_match.start - line_start].strip()
            if prefix:
                lines.append(
                    OcrLine(
                        text=prefix,
                        page_number=line.page_number,
                        bbox=list(line.bbox),
                        confidence=line.confidence,
                    )
                )
            break
        else:
            break
        offset = next_offset

    return OcrPage(
        page_number=page.page_number,
        width=page.width,
        height=page.height,
        lines=lines,
        text="\n".join(line.text for line in lines if line.text.strip()),
        ocr_time=page.ocr_time,
        image_path=page.image_path,
        processed_image_path=page.processed_image_path,
    )
