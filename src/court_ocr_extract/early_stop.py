from __future__ import annotations

from dataclasses import dataclass

from court_ocr_extract.marker_detection import detect_page_marker


@dataclass(frozen=True)
class MarkerDetection:
    found: bool
    page_index: int | None = None
    matched_text: str | None = None
    score: float = 0.0
    before_text: str = ""
    context: str = ""
    confidence: str = "none"
    line_index: int | None = None
    normalized_match: str | None = None


def find_marker_in_text(text: str, stop_marker: str) -> MarkerDetection:
    marker = detect_page_marker(page_number=1, marker_text=stop_marker, page_text=text or "")
    if not marker.found:
        return MarkerDetection(found=False, before_text=text or "")
    return MarkerDetection(
        found=True,
        matched_text=marker.matched_text,
        score={"high": 100.0, "medium": 90.0, "low": 70.0}.get(marker.confidence, 0.0),
        before_text=marker.before_text,
        context=marker.context,
        confidence=marker.confidence,
        line_index=marker.line_index,
        normalized_match=marker.normalized_match,
    )


def detect_marker_across_pages(page_texts: list[str], stop_marker: str) -> MarkerDetection:
    before: list[str] = []
    best = MarkerDetection(found=False)
    for index, text in enumerate(page_texts, start=1):
        detection = find_marker_in_text(text, stop_marker)
        if detection.found:
            return MarkerDetection(
                found=True,
                page_index=index,
                matched_text=detection.matched_text,
                score=detection.score,
                before_text="\n\n".join([*before, detection.before_text]).strip(),
                context=detection.context,
                confidence=detection.confidence,
                line_index=detection.line_index,
                normalized_match=detection.normalized_match,
            )
        before.append(text)
        if detection.score > best.score:
            best = detection
    return MarkerDetection(found=False, score=best.score, before_text="\n\n".join(before).strip())
