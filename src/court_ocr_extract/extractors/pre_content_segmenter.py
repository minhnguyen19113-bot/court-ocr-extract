from __future__ import annotations

import re
import unicodedata
from typing import Any

from court_ocr_extract.ocr_backends.base import OCRResult


DOCUMENT_TYPES = ("judgment_criminal_first_instance", "correction_notice", "unknown")


def route_document(text: str) -> dict[str, Any]:
    normalized = _fold(text)
    has_judgment = bool(re.search(r"\bban an\s*(?:so)?\b", normalized))
    has_people = "nhan danh" in normalized
    has_notice = bool(re.search(r"\bthong bao\b", normalized))
    has_correction = "sua chua bo sung ban an" in normalized or "sua chua, bo sung ban an" in normalized
    if has_notice and has_correction:
        return {"document_type": "correction_notice", "needs_review": False, "warnings": []}
    if has_judgment and has_people:
        return {"document_type": "judgment_criminal_first_instance", "needs_review": False, "warnings": []}
    return {
        "document_type": "unknown",
        "needs_review": True,
        "warnings": ["document_type_unknown"],
    }


def segment_pre_content(result: OCRResult, *, max_fallback_pages: int = 3) -> dict[str, Any]:
    lines = _filtered_lines(result)
    router = route_document("\n".join(str(line.get("text") or "") for line in lines))
    selected = []
    stop_line = None
    for line in lines:
        if _is_stop_heading(str(line.get("text") or "")):
            stop_line = line
            break
        if int(line.get("page_number") or 1) <= max_fallback_pages:
            selected.append(line)
    warnings = list(router["warnings"])
    if stop_line is None:
        warnings.append("pre_content_stop_heading_not_found_using_page_limit")
    pages = [int(line.get("page_number") or 1) for line in selected]
    return {
        "document_type": router["document_type"],
        "pre_content_lines": selected,
        "pre_content_text": "\n".join(str(line.get("text") or "") for line in selected).strip(),
        "start_page": min(pages) if pages else None,
        "end_page": max(pages) if pages else None,
        "stop_heading": str(stop_line.get("text")) if stop_line else None,
        "stop_line_id": str(stop_line.get("line_id")) if stop_line else None,
        "warnings": warnings,
        "needs_review": bool(router["needs_review"] or stop_line is None),
    }


def _filtered_lines(result: OCRResult) -> list[dict[str, Any]]:
    output = []
    for page in result.pages:
        for index, raw in enumerate(page.lines or [], start=1):
            line = dict(raw)
            line.setdefault("page_number", page.page_index)
            line.setdefault("line_id", f"p{page.page_index:03d}_l{index:04d}")
            output.append(line)
    if output:
        return output
    return [
        {"page_number": 1, "line_id": f"p001_l{index:04d}", "text": text}
        for index, text in enumerate(result.text.splitlines(), start=1) if text.strip()
    ]


def _is_stop_heading(text: str) -> bool:
    folded = _fold(text).strip(" .:-_")
    folded = re.sub(r"\s+", " ", folded)
    # A heading may contain numbering, but should not contain surrounding prose.
    return bool(re.fullmatch(r"(?:[ivx0-9]+[.)-]?\s*)?noi dung vu an", folded))


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^a-z0-9,.:;()\-/\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()
