from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable


CONFIDENCE_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}


@dataclass(frozen=True)
class MarkerResult:
    found: bool
    confidence: str = "none"
    page_number: int | None = None
    line_index: int | None = None
    matched_text: str | None = None
    normalized_match: str | None = None
    source: str | None = None
    before_text: str = ""
    context: str = ""

    @property
    def should_stop(self) -> bool:
        return self.found and self.confidence in {"high", "medium"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _TextMatch:
    confidence: str
    start: int
    end: int
    matched_text: str
    normalized_match: str


def normalize_marker_text(value: str) -> str:
    folded, _ = _fold_with_map(value)
    return folded


def detect_page_marker(
    *,
    page_number: int,
    marker_text: str,
    page_text: str = "",
    raw_lines: Iterable[dict[str, Any] | str] | None = None,
    filtered_lines: Iterable[dict[str, Any] | str] | None = None,
) -> MarkerResult:
    filtered_values = _line_values(filtered_lines)
    raw_values = _line_values(raw_lines)
    candidates = [
        *_line_candidates(filtered_values, "filtered_lines"),
        *_line_candidates(raw_values, "raw_lines"),
    ]
    if page_text:
        candidates.append((page_text, None, "page_text"))

    best: tuple[_TextMatch, int | None, str] | None = None
    for value, line_index, source in candidates:
        match = _match_marker(value, marker_text)
        if match is None:
            continue
        if best is None or CONFIDENCE_RANK[match.confidence] > CONFIDENCE_RANK[best[0].confidence]:
            best = (match, line_index, source)
        if match.confidence == "high" and source == "filtered_lines":
            break

    if best is None:
        return MarkerResult(found=False, page_number=page_number, before_text=page_text.strip())

    match, line_index, source = best
    canonical_match = _match_marker(page_text, marker_text) if page_text else None
    if canonical_match is not None and CONFIDENCE_RANK[canonical_match.confidence] >= 2:
        before_text = page_text[: canonical_match.start].strip()
        context = _context(page_text, canonical_match.start, canonical_match.end)
        if line_index is None:
            line_index = page_text[: canonical_match.start].count("\n")
    else:
        source_lines = filtered_values if source == "filtered_lines" else raw_values
        before_text = "\n".join(source_lines[: line_index or 0]).strip()
        context = match.matched_text

    return MarkerResult(
        found=True,
        confidence=match.confidence,
        page_number=page_number,
        line_index=line_index,
        matched_text=match.matched_text,
        normalized_match=match.normalized_match,
        source=source,
        before_text=before_text,
        context=context,
    )


def _match_marker(value: str, marker_text: str) -> _TextMatch | None:
    folded, index_map = _fold_with_map(value)
    marker = normalize_marker_text(marker_text)
    full = "".join(char for char in marker if char.isalnum())
    if not folded or not full:
        return None

    patterns: list[tuple[str, str]] = [("high", full)]
    if full == "noidungvuan":
        patterns.extend(
            [
                ("medium", "noidungvua"),
                ("medium", "noidungvu"),
                ("low", "noidung"),
            ]
        )
    for confidence, compact in patterns:
        found = re.search(_spaced_pattern(compact), folded)
        if found is None:
            continue
        start = index_map[found.start()]
        end = index_map[found.end() - 1] + 1
        return _TextMatch(
            confidence=confidence,
            start=start,
            end=end,
            matched_text=value[start:end].strip(),
            normalized_match=_words_for_compact(compact),
        )
    return None


def _spaced_pattern(compact: str) -> str:
    body = r"\s*".join(re.escape(char) for char in compact)
    return rf"(?<![a-z0-9]){body}(?![a-z0-9])"


def _words_for_compact(value: str) -> str:
    known = {
        "noidungvuan": "noi dung vu an",
        "noidungvua": "noi dung vu a",
        "noidungvu": "noi dung vu",
        "noidung": "noi dung",
    }
    return known.get(value, value)


def _fold_with_map(value: str) -> tuple[str, list[int]]:
    value = _repair_mojibake(unicodedata.normalize("NFKC", value or ""))
    output: list[str] = []
    index_map: list[int] = []
    pending_space: int | None = None
    for original_index, original_char in enumerate(value):
        char = original_char.replace("đ", "d").replace("Đ", "D")
        decomposed = unicodedata.normalize("NFKD", char)
        bases = [item for item in decomposed if unicodedata.category(item) != "Mn" and item.isalnum()]
        if not bases:
            if output:
                pending_space = original_index
            continue
        if pending_space is not None and output and output[-1] != " ":
            output.append(" ")
            index_map.append(pending_space)
        pending_space = None
        for item in bases:
            output.append(item.lower().replace("0", "o").replace("1", "i"))
            index_map.append(original_index)
    return "".join(output), index_map


def _line_values(lines: Iterable[dict[str, Any] | str] | None) -> list[str]:
    output: list[str] = []
    for line in lines or []:
        value = line if isinstance(line, str) else line.get("text", "")
        output.append(str(value or ""))
    return output


def _line_candidates(lines: list[str], source: str) -> list[tuple[str, int, str]]:
    output: list[tuple[str, int, str]] = []
    for index, line in enumerate(lines):
        output.append((line, index, source))
        if index + 1 < len(lines):
            output.append((f"{line}\n{lines[index + 1]}", index, source))
    return output


def _context(value: str, start: int, end: int) -> str:
    return value[max(0, start - 120) : min(len(value), end + 120)].strip()


def _repair_mojibake(value: str) -> str:
    if "Ã" not in value and "Â" not in value:
        return value
    try:
        return value.encode("cp1252").decode("utf-8")
    except (UnicodeError, LookupError):
        return value
