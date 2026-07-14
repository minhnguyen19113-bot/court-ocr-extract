from __future__ import annotations

import re
import unicodedata
from typing import Any


PARTICIPANT_ROLE_PATTERNS = (
    ("nguoi bao ve quyen va loi ich hop phap cua bi hai", "Người bảo vệ quyền và lợi ích hợp pháp của bị hại"),
    ("nguoi co quyen loi, nghia vu lien quan", "Người có quyền lợi, nghĩa vụ liên quan"),
    ("nguoi co quyen va nghia vu lien quan", "Người có quyền và nghĩa vụ liên quan"),
    ("nguoi bao chua cho bi cao", "Người bào chữa cho bị cáo"),
    ("nguoi giam ho cua bi cao", "Người giám hộ của bị cáo"),
    ("nguoi giam ho", "Người giám hộ"),
    ("nguoi lam chung", "Người làm chứng"),
    ("bi hai", "Bị hại"),
)

PARTICIPANT_NUMBER_PREFIX_RE = re.compile(r"^\s*(?:(?:\d+\.){2,}|\d+[.)])\s*")
INFORMATIONAL_ANCHOR_WARNINGS = frozenset(
    {"standalone_page_number_removed_from_defendant_blocks"}
)

DEFENDANT_BLOCKED_TERMS = (
    "qdxx",
    "quyet dinh",
    "thu ly",
    "xet xu so tham",
    "doi voi bi cao",
    "doi voi cac bi cao",
)


def segment_pre_content_anchors(segment: dict[str, Any], *, case_id: str) -> dict[str, Any]:
    lines = [_normalized_line(line) for line in segment.get("pre_content_lines", []) if _text(line)]
    warnings: list[str] = []
    metadata_lines = _metadata_region(lines)
    trial_panel_lines = _trial_panel_region(lines)
    defendant_blocks = _split_defendants(lines, warnings)
    participant_blocks = _split_participants(lines, warnings)
    if not metadata_lines:
        warnings.append("anchor_metadata_region_empty")
    if not trial_panel_lines:
        warnings.append("anchor_trial_panel_not_found")
    if not defendant_blocks:
        warnings.append("anchor_defendant_blocks_not_found")
    return {
        "case_id": case_id,
        "document_type": str(segment.get("document_type") or "unknown"),
        "metadata_lines": metadata_lines,
        "trial_panel_lines": trial_panel_lines,
        "defendant_blocks": defendant_blocks,
        "participant_blocks": participant_blocks,
        "warnings": _unique(warnings),
    }


def normalize_ocr_text(value: str) -> str:
    replacements = (
        (r"\bBản\s+ản\s+số\b", "Bản án số"),
        (r"\bTHÀNH\s+PHÔ\b", "THÀNH PHỐ"),
        (r"\bhọc\s+vẫn\b", "học vấn"),
        (r"\bcầm\s+đi\s+khỏi\s+nơi\s+cư\s+trú\b", "cấm đi khỏi nơi cư trú"),
        (r"\btam\s+giam\b", "tạm giam"),
    )
    result = value
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return re.sub(r"[–—−]", "-", result)


def fold_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", normalize_ocr_text(value).lower().replace("đ", "d"))
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9,.:;()/\-\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def participant_role(text: str) -> str | None:
    folded = fold_text(text).lstrip("- ")
    folded = PARTICIPANT_NUMBER_PREFIX_RE.sub("", folded)
    return next((role for anchor, role in PARTICIPANT_ROLE_PATTERNS if folded.startswith(anchor)), None)


def has_reviewable_warnings(warnings: list[str]) -> bool:
    return any(
        warning and warning not in INFORMATIONAL_ANCHOR_WARNINGS
        for warning in warnings
    )


def _metadata_region(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first_entity = next(
        (
            index
            for index, line in enumerate(lines)
            if _is_defendant_intro(_text(line)) or participant_role(_text(line))
        ),
        len(lines),
    )
    return lines[:first_entity]


def _trial_panel_region(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if "thanh phan hoi dong xet xu" in fold_text(_text(line))
            or "tham phan" in fold_text(_text(line))
        ),
        None,
    )
    if start is None:
        return []
    end = len(lines)
    for index in range(start + 1, len(lines)):
        folded = fold_text(_text(lines[index]))
        if "xet xu so tham cong khai" in folded or "thu ly so" in folded or _is_defendant_intro(_text(lines[index])):
            end = index
            break
    return lines[start:end]


def _split_defendants(lines: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    intro = next((i for i, line in enumerate(lines) if _is_defendant_intro(_text(line))), None)
    if intro is None:
        intro = next((i for i, line in enumerate(lines) if _defendant_start_reason(_text(line))), None)
    if intro is None:
        return []
    stop = next(
        (
            i
            for i in range(intro + 1, len(lines))
            if participant_role(_text(lines[i])) or "nhung nguoi tham gia to tung" in fold_text(_text(lines[i]))
        ),
        len(lines),
    )
    starts: list[tuple[int, str]] = []
    intro_text = _text(lines[intro])
    intro_value = _value_after_colon(intro_text)
    if _is_defendant_intro(intro_text) and intro_value:
        starts.append((intro, "intro_with_inline_defendant"))
    for index in range(intro + 1 if _is_defendant_intro(intro_text) else intro, stop):
        reason = _defendant_start_reason(_text(lines[index]))
        if reason:
            starts.append((index, reason))
    if not starts:
        first = next(
            (
                i
                for i in range(intro + 1, stop)
                if not _is_page_number(_text(lines[i]))
                and not any(term in fold_text(_text(lines[i])) for term in DEFENDANT_BLOCKED_TERMS)
            ),
            None,
        )
        if first is not None:
            starts.append((first, "single_defendant_after_intro"))
    blocks = []
    for position, (start, reason) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else stop
        block_lines = [line for line in lines[start:end] if not _is_page_number(_text(line))]
        if not block_lines:
            continue
        blocks.append(_block_payload("defendant", len(blocks) + 1, block_lines, reason))
    if any(_is_page_number(_text(line)) for line in lines[intro:stop]):
        warnings.append("standalone_page_number_removed_from_defendant_blocks")
    return blocks


def _split_participants(lines: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_role: str | None = None
    current_lines: list[dict[str, Any]] = []
    split_reason = ""

    def flush() -> None:
        nonlocal current_lines, split_reason
        if not current_lines:
            return
        payload = _block_payload("participant", len(blocks) + 1, current_lines, split_reason)
        payload["role_hint"] = current_role or ""
        blocks.append(payload)
        current_lines = []
        split_reason = ""

    for line in lines:
        text = _text(line)
        if _is_page_number(text):
            continue
        role = participant_role(text)
        if role:
            flush()
            current_role = role
            value = participant_inline_value(text, role)
            if value:
                current_lines = [line]
                split_reason = (
                    "numbered_participant_role_inline"
                    if _is_numbered_participant(text)
                    else "participant_role_inline"
                )
            continue
        if _is_numbered_participant(text):
            if not current_role:
                continue
            flush()
            current_lines = [line]
            split_reason = "numbered_participant"
            continue
        if not current_role:
            continue
        folded = fold_text(text)
        if _is_participant_continuation(folded):
            if current_lines:
                current_lines.append(line)
            continue
        if not current_lines:
            current_lines = [line]
            split_reason = "participant_after_heading"
            continue
        if _looks_like_person_line(text):
            flush()
            current_lines = [line]
            split_reason = "unnumbered_participant"
            continue
        current_lines.append(line)
    flush()
    if current_role and not blocks:
        warnings.append("participant_heading_without_person_block")
    return blocks


def _block_payload(prefix: str, index: int, lines: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    return {
        "block_id": f"{prefix}_{index:03d}",
        "line_ids": [_line_id(line) for line in lines],
        "text": "\n".join(_text(line) for line in lines),
        "start_line_id": _line_id(lines[0]),
        "end_line_id": _line_id(lines[-1]),
        "split_reason": reason,
    }


def _defendant_start_reason(text: str) -> str | None:
    folded = fold_text(text)
    if not folded or _is_page_number(text) or any(term in folded for term in DEFENDANT_BLOCKED_TERMS):
        return None
    if re.match(r"^bi cao\s*:\s*\S", folded):
        return "defendant_label"
    if re.match(r"^ho va ten\s*:\s*\S", folded):
        return "full_name_label"
    if re.match(r"^\d+[.)]\s*(?:ho va ten\s*:\s*)?\S", folded):
        return "numbered_defendant"
    if re.match(r"^[^:;,]{3,100},?\s+sinh\s+(?:ngay|nam)\b", folded):
        return "name_birth_pattern"
    return None


def _is_defendant_intro(text: str) -> bool:
    folded = fold_text(text).strip(" :.-")
    return bool(re.match(r"^doi voi(?:(?: cac)? bi cao)?(?:\s*:.*)?$", folded))


def participant_inline_value(text: str, role: str) -> str | None:
    value = strip_participant_numbering(normalize_ocr_text(text)).lstrip("- ")
    role_pattern = r"\s+".join(re.escape(part) for part in role.split())
    match = re.match(rf"^{role_pattern}\s*:?[\s-]*(.*)$", value, re.I)
    if not match:
        return _value_after_colon(value)
    remainder = match.group(1).strip(" -.;:")
    return remainder or None


def _is_participant_continuation(folded: str) -> bool:
    return folded.startswith(
        (
            "dia chi", "noi cu tru", "thuong tru", "noi o hien nay", "cung dia chi",
            "co mat", "vang mat", "co don xin vang mat", "sinh ngay", "sinh nam",
            "quan he", "ghi chu",
        )
    )


def _looks_like_person_line(text: str) -> bool:
    folded = fold_text(text)
    return bool(folded and not _is_participant_continuation(folded) and len(text) <= 220)


def _is_numbered_participant(text: str) -> bool:
    match = PARTICIPANT_NUMBER_PREFIX_RE.match(text)
    return bool(match and text[match.end():].strip())


def strip_participant_numbering(text: str) -> str:
    return PARTICIPANT_NUMBER_PREFIX_RE.sub("", text, count=1).strip()


def _normalized_line(line: dict[str, Any]) -> dict[str, Any]:
    output = dict(line)
    output["text"] = _text(line)
    output["normalized_text"] = normalize_ocr_text(output["text"])
    return output


def _value_after_colon(text: str) -> str | None:
    parts = re.split(r"[:：]", text, maxsplit=1)
    return parts[1].strip(" -.;") if len(parts) == 2 and parts[1].strip(" -.;") else None


def _is_page_number(text: str) -> bool:
    return bool(re.fullmatch(r"\s*\d{1,3}\s*", text))


def _text(line: dict[str, Any]) -> str:
    return str(line.get("text") or "").strip()


def _line_id(line: dict[str, Any]) -> str:
    return str(line.get("line_id") or "")


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
