from __future__ import annotations

import re
import unicodedata
from typing import Any


PARTICIPANT_ROLE_PATTERNS = (
    ("nguoi bao ve quyen va loi ich hop phap cua bi hai", "Người bảo vệ quyền và lợi ích hợp pháp của bị hại"),
    ("nguoi bao ve quyen va loi ich hop phap", "Người bảo vệ quyền và lợi ích hợp pháp"),
    ("nguoi co quyen loi va nghia vu lien quan", "Người có quyền lợi và nghĩa vụ liên quan"),
    ("nguoi co quyen loi, nghia vu lien quan", "Người có quyền lợi, nghĩa vụ liên quan"),
    ("nguoi co quyen va nghia vu lien quan", "Người có quyền và nghĩa vụ liên quan"),
    ("phap nhan thuong mai bi cao", "Pháp nhân thương mại bị cáo"),
    ("nguoi dai dien", "Người đại diện"),
    ("nguoi bao chua cho bi cao", "Người bào chữa cho bị cáo"),
    ("nguoi bao chua", "Người bào chữa"),
    ("nguoi giam ho cua bi cao", "Người giám hộ của bị cáo"),
    ("nguoi giam ho", "Người giám hộ"),
    ("nguoi phien dich", "Người phiên dịch"),
    ("nguoi giam dinh", "Người giám định"),
    ("nguoi dinh gia", "Người định giá"),
    ("nguoi chung kien", "Người chứng kiến"),
    ("nguoi lam chung", "Người làm chứng"),
    ("nguyen don dan su", "Nguyên đơn dân sự"),
    ("bi don dan su", "Bị đơn dân sự"),
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

DEFENDANT_INTRO_FOLDED_RE = re.compile(
    r"\bdoi\s+voi\s+(?:cac\s+)?bi\s+cao\s*[:：]",
    re.IGNORECASE,
)
DEFENDANT_INTRO_VALUE_RE = re.compile(
    r"\b(?:đối|đồi|đổi|doi)\s+(?:với|voi)\s+(?:(?:các|cac)\s+)?"
    r"(?:bị|bi)\s+(?:cáo|cao)\s*[:：]",
    re.IGNORECASE,
)
EXPLICIT_DEFENDANT_LABEL_FOLDED_RE = re.compile(
    r"^\s*(?:\d+[.)]\s*)?bi\s+cao\s*:\s*\S",
    re.IGNORECASE,
)
EXPLICIT_DEFENDANT_LABEL_VALUE_RE = re.compile(
    r"^\s*(?:\d+[.)]\s*)?(?:bị|bi)\s+(?:cáo|cao)\s*[:：]\s*(?P<value>.+)$",
    re.IGNORECASE,
)

DEFENDANT_PROFILE_PREFIXES = (
    "sinh ngay",
    "sinh nam",
    "noi sinh",
    "noi o",
    "cho o",
    "thuong tru",
    "ho khau thuong tru",
    "nghe nghiep",
    "trinh do",
    "quoc tich",
    "dan toc",
    "ton giao",
    "cccd",
    "cmnd",
    "can cuoc cong dan",
    "so dinh danh ca nhan",
)
IDENTITY_PROFILE_ANCHORS = (
    "sinh ngay",
    "sinh nam",
    "gioi tinh",
    "ho khau thuong tru",
    "thuong tru",
    "noi o",
    "cho o",
    "quoc tich",
    "dan toc",
    "ton giao",
    "nghe nghiep",
    "trinh do",
)


def segment_pre_content_anchors(segment: dict[str, Any], *, case_id: str) -> dict[str, Any]:
    lines = [_normalized_line(line) for line in segment.get("pre_content_lines", []) if _text(line)]
    warnings: list[str] = []
    metadata_lines = _metadata_region(lines)
    trial_panel_lines = _trial_panel_region(lines)
    participant_blocks = _split_participants(lines, warnings)
    defendant_blocks, defendant_region, rejected_defendant_candidates = _split_defendants(
        lines,
        warnings,
        metadata_lines=metadata_lines,
        trial_panel_lines=trial_panel_lines,
        participant_blocks=participant_blocks,
    )
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
        "defendant_region": defendant_region,
        "rejected_defendant_candidates": rejected_defendant_candidates,
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
    for index, line in enumerate(lines):
        if _is_defendant_intro(_text(line)):
            prefix = _text_before_defendant_intro(_text(line))
            return [
                *lines[:index],
                *([_line_with_text(line, prefix)] if prefix else []),
            ]
        if _is_explicit_defendant_label(_text(line)):
            return lines[:index]
        if participant_role(_text(line)):
            return lines[:index]
    return lines


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
        if (
            "xet xu so tham cong khai" in folded
            or "thu ly so" in folded
            or _is_defendant_intro(_text(lines[index]))
            or _is_explicit_defendant_label(_text(lines[index]))
        ):
            end = index
            break
    return lines[start:end]


def _split_defendants(
    lines: list[dict[str, Any]],
    warnings: list[str],
    *,
    metadata_lines: list[dict[str, Any]],
    trial_panel_lines: list[dict[str, Any]],
    participant_blocks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    intro = next((i for i, line in enumerate(lines) if _is_defendant_intro(_text(line))), None)
    fallback_intro = False
    if intro is None:
        intro = _find_explicit_defendant_fallback(lines, trial_panel_lines)
        fallback_intro = intro is not None
    region: dict[str, Any] = {
        "intro_found": intro is not None,
        "intro_line_id": _line_id(lines[intro]) if intro is not None else None,
        "start_line_id": None,
        "end_line_id": None,
        "stop_reason": None,
    }
    rejected: list[dict[str, Any]] = []
    if intro is None:
        return [], region, rejected
    stop = next(
        (
            i
            for i in range(intro + 1, len(lines))
            if participant_role(_text(lines[i])) or "nhung nguoi tham gia to tung" in fold_text(_text(lines[i]))
        ),
        len(lines),
    )
    region["stop_reason"] = "participant_region" if stop < len(lines) else "end_of_pre_content"
    region["end_line_id"] = _line_id(lines[stop - 1]) if stop > intro + 1 else None

    starts: list[tuple[int, str]] = []
    intro_text = _text(lines[intro])
    intro_value = (
        _explicit_defendant_label_value(intro_text)
        if fallback_intro
        else _defendant_intro_value(intro_text)
    )
    inline_reason = (
        "fallback_explicit_defendant_label"
        if fallback_intro and intro_value
        else _inline_defendant_reason(intro_value, lines[intro + 1:stop])
    )
    line_overrides: dict[int, dict[str, Any]] = {}
    if intro_value and inline_reason:
        starts.append((intro, inline_reason))
        line_overrides[intro] = _line_with_text(lines[intro], intro_value)
        region["start_line_id"] = _line_id(lines[intro])
    elif intro_value:
        rejected.append(
            _rejected_candidate(lines[intro], "inline_defendant_without_strong_identity_evidence")
        )

    for index in range(intro + 1, stop):
        reason = _defendant_start_reason(
            _text(lines[index]),
            following_lines=lines[index + 1:stop],
            defendant_region_established=True,
        )
        if reason:
            starts.append((index, reason))
        elif _looks_like_weak_numbered_person(_text(lines[index])):
            rejected.append(
                _rejected_candidate(lines[index], "numbered_line_without_identity_profile")
            )

    starts = list(dict.fromkeys(starts))
    if starts and region["start_line_id"] is None:
        region["start_line_id"] = _line_id(lines[starts[0][0]])

    forbidden_line_ids = {
        _line_id(line)
        for line in [*metadata_lines, *trial_panel_lines]
        if _line_id(line) and _line_id(line) != region["intro_line_id"]
    }
    forbidden_line_ids.update(
        line_id
        for block in participant_blocks
        for line_id in block.get("line_ids", [])
        if line_id
    )

    blocks: list[dict[str, Any]] = []
    for position, (start, reason) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else stop
        raw_block_lines = [line_overrides.get(index, lines[index]) for index in range(start, end)]
        block_lines = [line for line in raw_block_lines if not _is_page_number(_text(line))]
        if not block_lines:
            continue
        overlaps = [
            _line_id(line)
            for line in block_lines
            if _line_id(line) in forbidden_line_ids
        ]
        if overlaps:
            warnings.append("defendant_block_overlaps_forbidden_region")
            rejected.append(
                {
                    "line_ids": overlaps,
                    "text": "",
                    "reason": "defendant_block_overlaps_forbidden_region",
                }
            )
            continue
        if not _block_has_identity_evidence(block_lines, reason):
            rejected.append(
                {
                    "line_ids": [_line_id(line) for line in block_lines],
                    "text": "\n".join(_text(line) for line in block_lines),
                    "reason": "defendant_candidate_missing_identity_profile",
                }
            )
            continue
        blocks.append(_block_payload("defendant", len(blocks) + 1, block_lines, reason))
    if any(_is_page_number(_text(line)) for line in lines[intro:stop]):
        warnings.append("standalone_page_number_removed_from_defendant_blocks")
    return blocks, region, rejected


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


def _defendant_start_reason(
    text: str,
    *,
    following_lines: list[dict[str, Any]] | None = None,
    defendant_region_established: bool = False,
) -> str | None:
    folded = fold_text(text)
    if not folded or _is_page_number(text) or any(term in folded for term in DEFENDANT_BLOCKED_TERMS):
        return None
    if re.match(r"^(?:\d+[.)]\s*)?bi cao\s*:\s*\S", folded):
        return "defendant_label"
    if re.match(r"^(?:\d+[.)]\s*)?ho va ten\s*:\s*\S", folded):
        return "full_name_label"
    if re.match(r"^(?:\d+[.)]\s*)?[^:;,]{3,100},?\s+sinh\s+(?:ngay|nam)\b", folded):
        return "name_birth_pattern"
    if defendant_region_established and _numbered_person_with_inline_identity_profile(text):
        return "numbered_person_with_inline_identity_profile"
    if (
        defendant_region_established
        and _looks_like_weak_numbered_person(text)
        and _following_has_identity_profile(following_lines or [])
    ):
        return "numbered_person_with_profile_followup"
    return None


def _is_defendant_intro(text: str) -> bool:
    return bool(DEFENDANT_INTRO_FOLDED_RE.search(fold_text(text)))


def _is_explicit_defendant_label(text: str) -> bool:
    return bool(EXPLICIT_DEFENDANT_LABEL_FOLDED_RE.match(fold_text(text)))


def _defendant_intro_value(text: str) -> str | None:
    normalized = normalize_ocr_text(text)
    match = DEFENDANT_INTRO_VALUE_RE.search(normalized)
    if not match:
        return None
    value = normalized[match.end():].strip(" -.;:")
    return value or None


def _text_before_defendant_intro(text: str) -> str | None:
    normalized = normalize_ocr_text(text)
    match = DEFENDANT_INTRO_VALUE_RE.search(normalized)
    if not match:
        return None
    value = normalized[:match.start()].strip(" -.;:")
    return value or None


def _inline_defendant_reason(
    value: str | None,
    following_lines: list[dict[str, Any]],
) -> str | None:
    if not value:
        return None
    reason = _defendant_start_reason(
        value,
        following_lines=following_lines,
        defendant_region_established=True,
    )
    if reason:
        return "intro_inline_" + reason
    if _looks_like_person_line(value) and _following_has_identity_profile(following_lines):
        return "intro_inline_with_profile_followup"
    return None


def _looks_like_weak_numbered_person(text: str) -> bool:
    folded = fold_text(text)
    if not re.match(r"^\d+[.)]\s+\S", folded):
        return False
    remainder = re.sub(r"^\d+[.)]\s+", "", folded)
    return not any(prefix in remainder for prefix in DEFENDANT_PROFILE_PREFIXES)


def _numbered_person_with_inline_identity_profile(text: str) -> bool:
    folded = fold_text(text)
    match = re.match(r"^\d+[.)]\s+(?P<value>.+)$", folded)
    if match is None:
        return False
    value = match.group("value")
    anchors = _identity_profile_anchor_count(value)
    if not (re.search(r"\bsinh\s+(?:ngay|nam)\b", value) or anchors >= 2):
        return False
    first_anchor = re.search(
        r"\b(?:" + "|".join(re.escape(anchor) for anchor in IDENTITY_PROFILE_ANCHORS) + r")\b",
        value,
    )
    name = value[:first_anchor.start()] if first_anchor else value
    name_tokens = re.findall(r"[a-z]+", name)
    return len(name_tokens) >= 2


def _following_has_identity_profile(lines: list[dict[str, Any]]) -> bool:
    profile_lines: list[str] = []
    for line in lines:
        text = _text(line)
        if _is_page_number(text):
            continue
        if participant_role(text) or _is_defendant_intro(text):
            return False
        if _defendant_start_reason(text):
            return False
        profile_lines.append(text)
        if _has_identity_profile("\n".join(profile_lines)):
            return True
        if _looks_like_weak_numbered_person(text):
            return False
    return False


def _block_has_identity_evidence(lines: list[dict[str, Any]], reason: str) -> bool:
    if reason in {
        "defendant_label",
        "full_name_label",
        "intro_inline_defendant_label",
        "intro_inline_full_name_label",
        "fallback_explicit_defendant_label",
    }:
        return True
    return _has_identity_profile("\n".join(_text(line) for line in lines))


def _find_explicit_defendant_fallback(
    lines: list[dict[str, Any]],
    trial_panel_lines: list[dict[str, Any]],
) -> int | None:
    trial_line_ids = {_line_id(line) for line in trial_panel_lines}
    last_trial_index = max(
        (index for index, line in enumerate(lines) if _line_id(line) in trial_line_ids),
        default=-1,
    )
    for index, line in enumerate(lines):
        if index <= last_trial_index or not _is_explicit_defendant_label(_text(line)):
            continue
        if participant_role(_text(line)):
            return None
        value = _explicit_defendant_label_value(_text(line))
        if value and _fallback_has_identity_profile(value, lines[index + 1:]):
            return index
    return None


def _explicit_defendant_label_value(text: str) -> str | None:
    match = EXPLICIT_DEFENDANT_LABEL_VALUE_RE.match(normalize_ocr_text(text))
    if match is None:
        return None
    value = match.group("value").strip(" -.;:")
    return value or None


def _has_identity_profile(value: str) -> bool:
    folded = fold_text(value)
    return bool(
        re.search(r"\bsinh\s+(?:ngay|nam)\b", folded)
        or _identity_profile_anchor_count(folded) >= 2
    )


def _fallback_has_identity_profile(
    value: str,
    following_lines: list[dict[str, Any]],
) -> bool:
    profile_lines = [value]
    if _has_identity_profile(value):
        return True
    for line in following_lines:
        text = _text(line)
        if participant_role(text) or _is_defendant_intro(text) or _is_explicit_defendant_label(text):
            break
        profile_lines.append(text)
        if _has_identity_profile("\n".join(profile_lines)):
            return True
    return False


def _identity_profile_anchor_count(folded: str) -> int:
    return sum(
        bool(re.search(rf"\b{re.escape(anchor)}\b", folded))
        for anchor in IDENTITY_PROFILE_ANCHORS
    )


def _line_with_text(line: dict[str, Any], text: str) -> dict[str, Any]:
    output = dict(line)
    output["text"] = text
    output["normalized_text"] = normalize_ocr_text(text)
    return output


def _rejected_candidate(line: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "line_ids": [_line_id(line)],
        "text": _text(line),
        "reason": reason,
    }


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
