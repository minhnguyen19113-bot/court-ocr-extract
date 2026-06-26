from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from court_ocr_extract.postprocess.normalize_text import normalize_ocr_text


MARKER_NOI_DUNG = "NỘI DUNG VỤ ÁN"


@dataclass(frozen=True)
class MarkerMatch:
    found: bool
    start: int | None = None
    end: int | None = None
    text: str | None = None
    score: float = 0.0


@dataclass(frozen=True)
class SectionSplit:
    before_text: str
    after_text: str
    marker: MarkerMatch


def find_marker(text: str, threshold: float = 82, marker: str = MARKER_NOI_DUNG) -> MarkerMatch:
    normalized_text = normalize_ocr_text(text)
    spans = _line_spans(normalized_text)
    best = MarkerMatch(found=False)

    for index in range(len(spans)):
        for window_size in (1, 2, 3):
            window = spans[index : index + window_size]
            raw = " ".join(item[0] for item in window).strip()
            if not raw:
                continue
            score = _score_marker(raw, marker)
            if score > best.score:
                best = MarkerMatch(
                    found=score >= threshold,
                    start=window[0][1],
                    end=window[-1][2],
                    text=raw,
                    score=score,
                )
            if score >= 100:
                return best

    inline = _find_inline_marker(normalized_text, threshold, marker)
    if inline.found and inline.score >= best.score:
        return inline
    if best.found:
        return best
    return MarkerMatch(found=False, score=max(best.score, inline.score), text=best.text or inline.text)


def split_before_marker(text: str, threshold: float = 82, marker: str = MARKER_NOI_DUNG) -> SectionSplit:
    normalized_text = normalize_ocr_text(text)
    marker_match = find_marker(normalized_text, threshold=threshold, marker=marker)
    if marker_match.found and marker_match.start is not None and marker_match.end is not None:
        return SectionSplit(
            before_text=normalized_text[: marker_match.start].strip(),
            after_text=normalized_text[marker_match.end :].strip(),
            marker=marker_match,
        )
    return SectionSplit(before_text=normalized_text, after_text="", marker=marker_match)


def _find_inline_marker(text: str, threshold: float, marker: str) -> MarkerMatch:
    match_key = _match_key(text)
    marker_key = _match_key(marker)
    if marker_key and marker_key in match_key:
        raw_match = re.search(r"N[ỘO0]I\s+D[UƯ]NG\s+V[ỤU]\s+[ÁA]N\s*:?", text, flags=re.I)
        if raw_match:
            return MarkerMatch(
                found=True,
                start=raw_match.start(),
                end=raw_match.end(),
                text=raw_match.group(0),
                score=100.0,
            )

    candidates = [
        r"N[ỘO0]I\s+D[UƯ]NG\s+V[ỤU]\s+[ÁA]N\s*:?",
        r"NOI\s+DUNG\s+VU\s+AN\s*:?",
        r"N0I\s+DUNG\s+VU\s+AN\s*:?",
    ]
    for pattern in candidates:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(0)
            score = _score_marker(raw, marker)
            return MarkerMatch(
                found=score >= threshold,
                start=match.start(),
                end=match.end(),
                text=raw,
                score=score,
            )
    return MarkerMatch(found=False)


def _score_marker(value: str, marker: str = MARKER_NOI_DUNG) -> float:
    return _fuzzy_score(_match_key(value), _match_key(marker))


def _line_spans(text: str) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        raw_line = line.rstrip("\n")
        start = offset
        end = offset + len(raw_line)
        spans.append((raw_line, start, end))
        offset += len(line)
    return spans


def _match_key(value: str) -> str:
    value = unicodedata.normalize("NFD", _repair_mojibake(value).upper())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.replace("0", "O").replace("1", "I")
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _repair_mojibake(value: str) -> str:
    if "Ã" not in value and "áº" not in value and "á»" not in value:
        return value
    try:
        return value.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return value


def _fuzzy_score(left: str, right: str) -> float:
    try:
        from rapidfuzz import fuzz

        return float(fuzz.ratio(left, right))
    except Exception:
        return SequenceMatcher(None, left, right).ratio() * 100
