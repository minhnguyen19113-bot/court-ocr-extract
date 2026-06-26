from __future__ import annotations

import re
import unicodedata

from court_ocr_extract.postprocess.ocr_correction_rules import LEGAL_CORRECTIONS


def normalize_ocr_text(text: str) -> str:
    text = _repair_mojibake(text or "")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b\u200c\ufeff]", "", text)

    for source, target in LEGAL_CORRECTIONS:
        text = text.replace(source, target)

    text = _join_split_vietnamese_dates(text)
    text = _normalize_line_spaces(text)
    text = _join_soft_wrapped_lines(text)
    return text.strip()


def _repair_mojibake(value: str) -> str:
    if "Ã" not in value and "áº" not in value and "á»" not in value and "Ä" not in value:
        return value
    try:
        return value.encode("cp1252").decode("utf-8")
    except UnicodeError:
        return value


def _join_split_vietnamese_dates(text: str) -> str:
    patterns = [
        (
            r"\bngày\s+(\d{1,2})\s*\n+\s*tháng\s+(\d{1,2})\s*\n+\s*năm\s+(\d{4})",
            r"ngày \1 tháng \2 năm \3",
        ),
        (r"\bngày\s+(\d{1,2})\s*\n+\s*tháng\s+(\d{1,2})", r"ngày \1 tháng \2"),
        (r"\btháng\s+(\d{1,2})\s*\n+\s*năm\s+(\d{4})", r"tháng \1 năm \2"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _normalize_line_spaces(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")
    return "\n".join(lines)


def _join_soft_wrapped_lines(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    result: list[str] = []
    for line in lines:
        if not result or not line:
            result.append(line)
            continue
        previous = result[-1]
        if not previous:
            result.append(line)
            continue
        if _should_join(previous, line):
            result[-1] = f"{previous} {line}"
        else:
            result.append(line)
    return "\n".join(result)


def _should_join(previous: str, current: str) -> bool:
    if re.search(r"[:;.?!]$", previous):
        return False
    if re.match(
        r"^(Bị cáo|Bị hại|Người có quyền lợi|Thẩm phán|Hội thẩm|Kiểm sát viên|NỘI DUNG)",
        current,
        flags=re.IGNORECASE,
    ):
        return False
    if re.match(r"^\d+[.)]\s+", current):
        return False
    if current[:1].islower():
        return True
    return bool(re.search(r"\b(ngày|tháng|năm|sinh|trú|cư trú|địa chỉ)$", previous, re.I))
