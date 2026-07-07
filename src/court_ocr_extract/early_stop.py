from __future__ import annotations

from dataclasses import dataclass

from court_ocr_extract.postprocess.section_splitter import find_marker


@dataclass(frozen=True)
class MarkerDetection:
    found: bool
    page_index: int | None = None
    matched_text: str | None = None
    score: float = 0.0
    before_text: str = ""
    context: str = ""


def find_marker_in_text(text: str, stop_marker: str) -> MarkerDetection:
    marker = find_marker(text or "", marker=stop_marker)
    if not marker.found or marker.start is None:
        return MarkerDetection(found=False, score=marker.score, before_text=text or "")
    start = max(marker.start - 120, 0)
    end = min((marker.end or marker.start) + 120, len(text))
    return MarkerDetection(
        found=True,
        matched_text=marker.text,
        score=marker.score,
        before_text=text[: marker.start].strip(),
        context=text[start:end].strip(),
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
            )
        before.append(text)
        if detection.score > best.score:
            best = detection
    return MarkerDetection(found=False, score=best.score, before_text="\n\n".join(before).strip())
