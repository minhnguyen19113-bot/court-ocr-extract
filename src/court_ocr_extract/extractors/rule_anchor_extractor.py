from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from court_ocr_extract.extractors.pre_content_anchor_segmenter import (
    DEFENDANT_BLOCKED_TERMS,
    fold_text,
    has_reviewable_warnings,
    normalize_ocr_text,
    participant_inline_value,
    participant_role,
    strip_participant_numbering,
)
from court_ocr_extract.extractors.pre_content_schema import (
    DEFENDANT_FIELDS,
    PARTICIPANT_FIELDS,
    empty_pre_content_output,
)
from court_ocr_extract.extractors.rule_parser import (
    extract_identity_number,
    parse_vietnamese_date,
)
from court_ocr_extract.source_region_policy import FRONT_PRE_CONTENT


DATE_RE = re.compile(r"\b(\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4})\b")
JUDGMENT_NUMBER_RE = re.compile(r"Bản\s+án\s+số\s*[:.]?\s*([0-9]{1,4}/[0-9]{4}/HS-?ST)\b", re.I)
CASE_NUMBER_TOKEN_RE = re.compile(
    r"([0-9]{1,4}\s*/\s*[0-9]{4}\s*/\s*[0-9A-Za-zÀ-ỹĐđ-]+)",
    re.I,
)
PRESENCE_SUFFIX_RE = re.compile(
    r"\s*(?:[-–—;]?\s*(?:có\s+đơn\s+xin\s+vắng\s+mặt|có\s+mặt|vắng\s+mặt)"
    r"|\(\s*(?:có\s+đơn\s+xin\s+vắng\s+mặt|có\s+mặt|vắng\s+mặt)\s*\))\s*$",
    re.I,
)
SHORT_FIELDS = ("gender", "nationality", "ethnicity", "religion", "occupation")
DEFENDANT_IDENTITY_FIELDS = (
    "birth_date_or_year",
    "birth_place",
    "permanent_address",
    "current_address",
    "occupation",
    "education",
    "cccd",
)
MULTI_PERSON_ROLE_PREFIXES = (
    "nguoi giam ho",
    "nguoi dai dien",
    "nguoi bao chua",
    "nguoi bao ve quyen va loi ich hop phap",
)
HONORIFIC_RE = re.compile(r"\b(?:Ông|Bà|Anh|Chị)\s+", re.IGNORECASE)
LEADING_HONORIFIC_RE = re.compile(r"^\s*(?:Ông|Bà|Anh|Chị)\s+", re.IGNORECASE)

PANEL_LABELS = (
    (re.compile(r"(?:Thẩm\s+phán(?:\s*-\s*Chủ\s+tọa\s+phiên\s+tòa)?|Chủ\s+tọa\s+phiên\s+tòa)(?=\s*(?::|$))", re.I), "presiding_judge"),
    (re.compile(r"(?:Các\s+)?Hội\s+thẩm\s+nhân\s+dân(?=\s*(?::|$))", re.I), "jurors"),
    (re.compile(r"Thư\s+ký\s+phiên\s+tòa(?=\s*(?::|$))", re.I), "clerk"),
    (re.compile(r"(?:Đại\s+diện\s+Viện\s+kiểm\s+sát[^:;]*|Kiểm\s+sát\s+viên)(?=\s*(?::|$))", re.I), "prosecutor"),
)

DEFENDANT_LABELS = (
    (
        "current_address",
        re.compile(
            r"Chỗ\s+ở(?:\s+hiện\s+tại)?|Nơi\s+ở(?:\s+hiện\s+tại|\s+hiện\s+nay)?"
            r"|Nơi\s+cư\s+trú|Địa\s+chỉ",
            re.I,
        ),
    ),
    ("permanent_address", re.compile(r"Hộ\s+khẩu\s+thường\s+trú|Thường\s+trú|Nơi\s+đăng\s+ký\s+HKTT|Nơi\s+ĐKHKTT", re.I)),
    ("education", re.compile(r"Trình\s+độ\s+(?:văn\s+hóa|học\s+vấn)", re.I)),
    ("criminal_record", re.compile(r"Tiền\s+án\s*[,\-]\s*tiền\s+sự|Tiền\s+án|Tiền\s+sự", re.I)),
    ("birth_place", re.compile(r"Nơi\s+sinh", re.I)),
    ("birth_date_or_year", re.compile(r"Sinh\s+(?:ngày|năm)", re.I)),
    ("alias", re.compile(r"Tên\s+gọi\s+khác", re.I)),
    ("occupation", re.compile(r"Nghề\s+nghiệp", re.I)),
    ("nationality", re.compile(r"Quốc\s+tịch", re.I)),
    ("ethnicity", re.compile(r"Dân\s+tộc", re.I)),
    ("religion", re.compile(r"Tôn\s+giáo", re.I)),
    ("gender", re.compile(r"Giới\s+tính", re.I)),
    ("father_name", re.compile(r"Họ\s+(?:và\s+)?tên\s+cha|Cha", re.I)),
    ("mother_name", re.compile(r"Họ\s+(?:và\s+)?tên\s+mẹ|Mẹ", re.I)),
    ("spouse", re.compile(r"Vợ\s*[,/]\s*con|Vợ|Chồng", re.I)),
    ("children", re.compile(r"Con(?!\s+ông\b)", re.I)),
)

CURRENT_ADDRESS_LABEL_PATTERN = (
    r"(?:Chỗ\s+ở(?:\s+hiện\s+tại)?|Nơi\s+ở(?:\s+hiện\s+tại|\s+hiện\s+nay)?"
    r"|Nơi\s+cư\s+trú|Địa\s+chỉ)"
)
ADDRESS_STOP_LABEL_PATTERN = (
    r"(?:Nghề\s+nghiệp|Trình\s+độ(?:\s+văn\s+hóa)?|Dân\s+tộc|Giới\s+tính"
    r"|Tôn\s+giáo|Quốc\s+tịch|Cha|Mẹ|con\s+ông|con\s+bà|Vợ|Chồng"
    r"|Vợ\s+con|Con|Tiền\s+án|Tiền\s+sự|Nhân\s+thân|Bị\s+cáo\s+bị)"
)
CURRENT_ADDRESS_LINE_RE = re.compile(
    rf"^{CURRENT_ADDRESS_LABEL_PATTERN}\s*[:：]?\s*(.*)$",
    re.IGNORECASE,
)
CURRENT_ADDRESS_SEARCH_RE = re.compile(
    rf"{CURRENT_ADDRESS_LABEL_PATTERN}\s*[:：]?\s*(.*)$",
    re.IGNORECASE,
)
ADDRESS_STOP_LABEL_RE = re.compile(
    rf"^{ADDRESS_STOP_LABEL_PATTERN}\s*[:：]",
    re.IGNORECASE,
)
ADDRESS_STOP_INLINE_RE = re.compile(
    rf"(?:^|[;.\n])\s*{ADDRESS_STOP_LABEL_PATTERN}\s*[:：]",
    re.IGNORECASE,
)
CURRENT_ADDRESS_FLAT_RE = re.compile(
    rf"{CURRENT_ADDRESS_LABEL_PATTERN}\s*[:：]?\s*(?P<value>.*?)"
    rf"(?=(?:\n|;|\.)\s*{ADDRESS_STOP_LABEL_PATTERN}\s*[:：]"
    rf"|\n\s*(?:\d+[.)]\s+.*\b(?:sinh\s+ngày|sinh\s+năm)\b|Bị\s+cáo\s+\S)"
    rf"|\Z)",
    re.IGNORECASE | re.DOTALL,
)
STANDALONE_PAGE_NUMBER_RE = re.compile(r"^\s*(?:trang\s+)?\d+\s*$", re.IGNORECASE)
NEXT_DEFENDANT_RE = re.compile(
    r"^\s*(?:\d+[.)]\s+.*\b(?:sinh\s+ngày|sinh\s+năm)\b|Bị\s+cáo\s+\S)",
    re.IGNORECASE,
)
PARTICIPANT_ADDRESS_PATTERNS = (
    re.compile(r"(?:Nơi\s+ở\s+hiện\s+tại|Nơi\s+ở\s+hiện\s+nay|Chỗ\s+ở)\s*[:：]?", re.I),
    re.compile(r"(?:Địa\s+chỉ|Cùng\s+địa\s+chỉ)\s*[:：]?", re.I),
    re.compile(r"Nơi\s+cư\s+trú\s*[:：]?", re.I),
    re.compile(r"(?:Hộ\s+khẩu\s+)?Thường\s+trú\s*[:：]?", re.I),
)
PARTICIPANT_ADDRESS_STOP_RE = re.compile(
    rf"(?:[;.\n])\s*(?:{ADDRESS_STOP_LABEL_PATTERN}|Quan\s+hệ|Ghi\s+chú|"
    r"Sinh\s+(?:ngày|năm)|Có\s+mặt|Vắng\s+mặt|Có\s+đơn\s+xin\s+vắng\s+mặt)\s*[:：]?",
    re.I,
)


def extract_rule_anchor_output(anchor: dict[str, Any]) -> dict[str, Any]:
    output = empty_pre_content_output(str(anchor.get("document_type") or "unknown"))
    _extract_metadata(anchor.get("metadata_lines", []), output)
    _extract_trial_panel(anchor.get("trial_panel_lines", []), output)
    rejected_defendants = []
    for block in anchor.get("defendant_blocks", []):
        defendant = parse_defendant_block(block)
        if defendant.get("entity_valid"):
            output["defendants"].append(defendant)
        else:
            rejected_defendants.append(defendant)
            output["warnings"].append(
                f"defendant_entity_rejected:{block.get('block_id') or 'unknown'}"
            )
    output["rejected_defendant_entities"] = rejected_defendants
    for block in anchor.get("participant_blocks", []):
        output["participants"].extend(parse_participant_block_entities(block))
    output["warnings"].extend(anchor.get("warnings", []))
    if not output["metadata"]["judgment_number"]:
        output["warnings"].append("missing:metadata.judgment_number")
    if not output["trial_panel"]["presiding_judge"]:
        output["warnings"].append("missing:trial_panel.presiding_judge")
    output["needs_review"] = bool(
        has_reviewable_warnings(output["warnings"])
        or any(item.get("needs_review") for item in output["defendants"] + output["participants"])
    )
    output.update(
        strategy="rule_anchor_only",
        status="rule_anchor_succeeded",
        result_valid=True,
        llm_json_valid=False,
        llm_actually_called=False,
        llm_status=[],
        chunk_count=0,
        anchor_segments=anchor,
    )
    return output


def parse_defendant_block(block: dict[str, Any]) -> dict[str, Any]:
    result = {field: None for field in DEFENDANT_FIELDS}
    raw_source = str(block.get("text") or "")
    raw = normalize_ocr_text(raw_source)
    line_ids = [str(value) for value in block.get("line_ids", []) if value]
    result.update(
        raw_block=raw_source,
        evidence_line_ids=line_ids,
        source_block_id=str(block.get("block_id") or ""),
        entity_id=str(block.get("block_id") or ""),
        source_region=FRONT_PRE_CONTENT,
        split_reason=str(block.get("split_reason") or ""),
        needs_review=False,
        warnings=[],
    )
    result["full_name"] = _defendant_name(raw)
    _extract_defendant_labeled_values(raw, result)
    _parse_spouse_children(raw, result)
    _parse_current_address(block, raw, result)
    result["cccd"] = extract_identity_number(raw)

    parent_match = re.search(r"con\s+ông\s+(.+?)\s+và\s+bà\s+([^,;.\n]+)", raw, re.I)
    if parent_match:
        result["father_name"] = _clean_value(parent_match.group(1))
        result["mother_name"] = _clean_value(parent_match.group(2))
    birth_place = re.search(
        r"Sinh\s+(?:ngày\s+\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4}|năm\s+\d{4})\s+tại\s*:\s*([^;\n]+)",
        raw,
        re.I,
    )
    if birth_place and not result["birth_place"]:
        result["birth_place"] = _clean_value(birth_place.group(1))
    for line in raw.splitlines():
        folded = fold_text(line)
        if not result["detention_status"] and any(value in folded for value in ("tam giam", "tam giu", "cam di khoi noi cu tru")):
            result["detention_status"] = line.strip()
        if not result["presence_status"] and ("bi cao co mat" in folded or "bi cao vang mat" in folded):
            result["presence_status"] = _presence(line)

    validate_defendant_entity(result)
    return result


def parse_participant_block(block: dict[str, Any]) -> dict[str, Any]:
    result = {field: None for field in PARTICIPANT_FIELDS}
    result["relationship_or_note"] = None
    raw_source = str(block.get("text") or "")
    raw = normalize_ocr_text(raw_source)
    line_ids = [str(value) for value in block.get("line_ids", []) if value]
    role = str(block.get("role_hint") or "").strip() or None
    result.update(
        role=role,
        raw_block=raw_source,
        evidence_line_ids=line_ids,
        source_block_id=str(block.get("block_id") or ""),
        entity_id=str(block.get("block_id") or ""),
        source_region=FRONT_PRE_CONTENT,
        needs_review=False,
        warnings=[],
    )
    primary_line = _participant_primary_line(raw, role)
    result["full_name"] = _participant_name(primary_line)
    result["cccd"] = extract_identity_number(raw)
    result["represented_person"] = _participant_represented_person(raw, role)
    birth = re.search(r"\b(?:sinh\s+ngày\s+)?(\d{1,2}\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4})\b|\bsinh\s+năm\s+(\d{4})\b", raw, re.I)
    if birth:
        result["birth_date_or_year"] = _normalize_date(birth.group(1)) if birth.group(1) else birth.group(2)
    result["address"] = _participant_address(raw)
    relationship = re.search(r"(?:Quan\s+hệ|Ghi\s+chú)\s*[:：]\s*([^;\n]+)", raw, re.I)
    if relationship:
        result["relationship"] = _clean_value(relationship.group(1))
        result["relationship_or_note"] = result["relationship"]
    inline_note = _participant_relationship_note(primary_line)
    if inline_note:
        existing = result.get("relationship_or_note")
        combined = "; ".join(dict.fromkeys(value for value in (existing, inline_note) if value))
        result["relationship"] = combined
        result["relationship_or_note"] = combined
    presence_line = next(
        (line for line in raw.splitlines() if "co mat" in fold_text(line) or "vang mat" in fold_text(line)),
        None,
    )
    if presence_line:
        result["presence_status"] = _presence(presence_line)
    validate_participant_entity(result)
    return result


def parse_participant_block_entities(block: dict[str, Any]) -> list[dict[str, Any]]:
    base = parse_participant_block(block)
    role = str(base.get("role") or "")
    if not any(fold_text(role).startswith(prefix) for prefix in MULTI_PERSON_ROLE_PREFIXES):
        return [base]
    primary_line = _participant_primary_line(
        normalize_ocr_text(str(block.get("text") or "")),
        role,
    )
    names, shared_note = _multi_person_names(primary_line)
    if len(names) < 2:
        return [base]
    entities = []
    for name in names:
        entity = deepcopy(base)
        entity["full_name"] = name
        entity["relationship"] = shared_note
        entity["relationship_or_note"] = shared_note
        entity["warnings"] = []
        entity["needs_review"] = False
        validate_participant_entity(entity)
        entities.append(entity)
    return entities


def _extract_metadata(lines: list[dict[str, Any]], output: dict[str, Any]) -> None:
    judgment_index = None
    for index, line in enumerate(lines):
        text = normalize_ocr_text(_text(line))
        folded = fold_text(text)
        if not output["metadata"]["court_name"] and "toa an" in folded and "cong hoa" not in folded:
            _set(output, "metadata.court_name", text, line, 0.98)
        judgment = JUDGMENT_NUMBER_RE.search(text)
        if judgment and not output["metadata"]["judgment_number"]:
            judgment_index = index
            _set(output, "metadata.judgment_number", judgment.group(1), line, 0.99)
            same_line_date = _date_after_day_anchor(text)
            if same_line_date:
                _set(output, "metadata.judgment_date", same_line_date, line, 0.98)
        if "quyet dinh dua vu an ra xet xu so" in folded:
            value = _number_after_anchor(text, r"Quyết\s+định\s+đưa\s+vụ\s+án\s+ra\s+xét\s+xử\s+số")
            _set(output, "metadata.trial_decision_number", value, line, 0.97)
        if "quyet dinh hoan phien toa so" in folded:
            value = _number_after_anchor(text, r"Quyết\s+định\s+hoãn\s+phiên\s+tòa\s+số")
            _set(output, "metadata.postponement_decision_number", value, line, 0.97)
        if "thu ly so" in folded:
            value, acceptance_tail = _number_and_tail_after_anchor(
                text,
                r"thụ\s+lý\s+số",
            )
            _set(output, "metadata.case_acceptance_number", value, line, 0.96)
            if value:
                acceptance_date = parse_vietnamese_date(acceptance_tail or "")
                _set(output, "metadata.case_acceptance_date", acceptance_date, line, 0.96)
            elif not output["metadata"].get("case_acceptance_number"):
                output["warnings"].append(
                    "acceptance_date_blocked_missing_acceptance_number"
                )
        if (
            not output["metadata"]["trial_location_or_date_sentence"]
            and "xet xu so tham" in folded
            and ("ngay" in folded or "tai" in folded)
        ):
            _set(output, "metadata.trial_location_or_date_sentence", text, line, 0.82)
    if judgment_index is not None and not output["metadata"]["judgment_date"] and judgment_index + 1 < len(lines):
        next_line = normalize_ocr_text(_text(lines[judgment_index + 1]))
        if re.match(r"^\s*Ngày\s*:", next_line, re.I):
            date = _date_after_day_anchor(next_line)
            _set(output, "metadata.judgment_date", date, lines[judgment_index + 1], 0.97)
    number = str(output["metadata"].get("judgment_number") or "")
    if "HS" in number.upper():
        output["metadata"]["case_type"] = "Hình sự sơ thẩm"


def _extract_trial_panel(lines: list[dict[str, Any]], output: dict[str, Any]) -> None:
    active_field: str | None = None
    for line in lines:
        text = normalize_ocr_text(_text(line))
        matches = []
        for pattern, field in PANEL_LABELS:
            matches.extend((match.start(), match.end(), field) for match in pattern.finditer(text))
        matches.sort()
        if matches:
            active_field = None
            for index, (_, end, field) in enumerate(matches):
                next_start = matches[index + 1][0] if index + 1 < len(matches) else len(text)
                value = _clean_panel_value(
                    text[end:next_start],
                    preserve_newlines=field == "jurors",
                )
                if value:
                    _set_panel(output, field, value, line)
                else:
                    active_field = field
            continue
        if active_field and text and not re.match(r"^Thành\s+phần", text, re.I):
            value = re.sub(r"^\s*\d+[.)]\s*", "", text).strip()
            _set_panel(output, active_field, value, line)
            if active_field != "jurors":
                active_field = None


def _extract_defendant_labeled_values(raw: str, result: dict[str, Any]) -> None:
    matches: list[tuple[int, int, str]] = []
    for field, pattern in DEFENDANT_LABELS:
        matches.extend((match.start(), match.end(), field) for match in pattern.finditer(raw))
    matches.sort()
    for index, (_, end, field) in enumerate(matches):
        if result.get(field):
            continue
        next_start = matches[index + 1][0] if index + 1 < len(matches) else len(raw)
        value = _clean_value(raw[end:next_start])
        if field == "birth_date_or_year":
            date = DATE_RE.search(value or "")
            year = re.search(r"\b(?:19|20)\d{2}\b", value or "")
            value = _normalize_date(date.group(1)) if date else (year.group(0) if year else None)
        if value:
            result[field] = value


def _parse_spouse_children(raw: str, result: dict[str, Any]) -> None:
    combined = re.search(r"Vợ\s*[,/]?\s*con\s*[:：]\s*([^\n]+)", raw, re.I)
    if not combined:
        return
    value = combined.group(1).strip(" .;,")
    spouse = re.search(
        r"\b(chưa\s+có\s+vợ|chưa\s+có\s+chồng|có\s+vợ|có\s+chồng)\b",
        value,
        re.I,
    )
    children = re.search(
        r"\b(\d{1,2}\s+con(?:\s+sinh\s+năm\s+\d{4})?)\b",
        value,
        re.I,
    )
    result["spouse"] = _clean_value(spouse.group(1)) if spouse else None
    result["children"] = _clean_value(children.group(1)) if children else None


def _parse_current_address(
    block: dict[str, Any],
    raw: str,
    result: dict[str, Any],
) -> None:
    value, used_line_ids = _collect_current_address_lines(block, raw)
    if not value:
        value, used_line_ids = _collect_current_address_flat(block, raw)
    if not value:
        return
    result["current_address"] = value
    result["current_address_evidence_line_ids"] = list(used_line_ids)
    result["evidence_line_ids"] = list(
        dict.fromkeys([*result.get("evidence_line_ids", []), *used_line_ids])
    )


def _collect_current_address_lines(
    block: dict[str, Any],
    raw: str,
) -> tuple[str, list[str]]:
    lines = raw.splitlines()
    line_ids = [str(value) for value in block.get("line_ids", [])]
    for index, line in enumerate(lines):
        match = CURRENT_ADDRESS_SEARCH_RE.search(line.strip())
        if not match:
            continue
        first_value, stopped = _address_fragment(match.group(1))
        values = [first_value] if first_value else []
        used_line_ids = [line_ids[index]] if index < len(line_ids) else []
        if not stopped:
            for continuation_index in range(index + 1, len(lines)):
                continuation = lines[continuation_index].strip()
                if not continuation:
                    continue
                if STANDALONE_PAGE_NUMBER_RE.match(continuation):
                    continue
                if _is_address_stop_line(continuation):
                    break
                fragment, stopped = _address_fragment(continuation)
                if fragment:
                    values.append(fragment)
                    if continuation_index < len(line_ids):
                        used_line_ids.append(line_ids[continuation_index])
                if stopped:
                    break
        return _normalize_current_address(" ".join(values)), used_line_ids
    return "", []


def _collect_current_address_flat(
    block: dict[str, Any],
    raw: str,
) -> tuple[str, list[str]]:
    match = CURRENT_ADDRESS_FLAT_RE.search(raw)
    if match is None:
        return "", []
    start_line = raw[:match.start("value")].count("\n")
    line_ids = [str(value) for value in block.get("line_ids", [])]
    values: list[str] = []
    used_line_ids: list[str] = []
    for offset, line in enumerate(match.group("value").splitlines()):
        value = line.strip()
        if not value or STANDALONE_PAGE_NUMBER_RE.match(value):
            continue
        values.append(value)
        line_index = start_line + offset
        if line_index < len(line_ids):
            used_line_ids.append(line_ids[line_index])
    return _normalize_current_address(" ".join(values)), used_line_ids


def _address_fragment(value: str) -> tuple[str, bool]:
    stop = ADDRESS_STOP_INLINE_RE.search(value)
    if stop is None:
        return value.strip(), False
    return value[:stop.start()].strip(), True


def _participant_address(raw: str) -> str | None:
    for pattern in PARTICIPANT_ADDRESS_PATTERNS:
        match = pattern.search(raw)
        if match is None:
            continue
        value = raw[match.end():]
        stop = PARTICIPANT_ADDRESS_STOP_RE.search(value)
        if stop is not None:
            value = value[:stop.start()]
        value = PRESENCE_SUFFIX_RE.sub("", value)
        value = re.sub(r"\s+", " ", value).strip(" ,;:.-")
        if value:
            return value
    return None


def _normalize_current_address(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" ,;:.-")
    return re.sub(
        r"^(?:hiện\s+tại|hiện\s+nay)\s*[:：]\s*",
        "",
        normalized,
        flags=re.IGNORECASE,
    ).strip(" ,;:.-")


def _is_address_stop_line(value: str) -> bool:
    if CURRENT_ADDRESS_LINE_RE.match(value):
        return True
    if ADDRESS_STOP_LABEL_RE.match(value) or NEXT_DEFENDANT_RE.match(value):
        return True
    return any(pattern.match(value) for _, pattern in DEFENDANT_LABELS)


def _defendant_name(raw: str) -> str | None:
    for line in raw.splitlines():
        candidate = re.sub(r"^\s*\d+[.)]\s*", "", line).strip()
        candidate = re.sub(r"^(?:Đối\s+với(?:\s+các)?\s+bị\s+cáo|Bị\s+cáo|Họ\s+và\s+tên)\s*:\s*", "", candidate, flags=re.I)
        candidate = re.split(
            r"(?:[,;]\s*|\s+)(?:sinh\s+(?:ngày|năm)|tên\s+gọi\s+khác|"
            r"giới\s+tính|hộ\s+khẩu\s+thường\s+trú|thường\s+trú|nơi\s+ở|"
            r"chỗ\s+ở|quốc\s+tịch|dân\s+tộc|tôn\s+giáo|nghề\s+nghiệp|trình\s+độ)",
            candidate,
            maxsplit=1,
            flags=re.I,
        )[0]
        candidate = candidate.strip(" ,;:-")
        if candidate and not any(term in fold_text(candidate) for term in DEFENDANT_BLOCKED_TERMS):
            return candidate
    return None


def _participant_primary_line(raw: str, role: str | None) -> str | None:
    for line in raw.splitlines():
        text = strip_participant_numbering(line).strip()
        detected_role = participant_role(text)
        if detected_role:
            text = participant_inline_value(text, detected_role) or ""
        if not text or _is_participant_detail_line(text):
            continue
        return text
    return None


def _participant_name(primary_line: str | None) -> str | None:
    if not primary_line:
        return None
    candidate = PRESENCE_SUFFIX_RE.sub("", primary_line).strip(" ,;:-")
    candidate = re.split(r"\s*\([^)]*\)", candidate, maxsplit=1)[0]
    candidate = re.split(r"[,;]", candidate, maxsplit=1)[0]
    candidate = re.split(r"\s+sinh\s+(?:ngày|năm)\b", candidate, maxsplit=1, flags=re.I)[0]
    candidate = LEADING_HONORIFIC_RE.sub("", candidate)
    return _clean_value(candidate)


def _participant_relationship_note(primary_line: str | None) -> str | None:
    if not primary_line:
        return None
    without_presence = PRESENCE_SUFFIX_RE.sub("", primary_line).strip(" ,;:-")
    notes = [_clean_value(value) for value in re.findall(r"\(([^)]+)\)", without_presence)]
    if "," in without_presence:
        tail = _clean_value(without_presence.split(",", 1)[1])
        if tail and not fold_text(tail).startswith(("sinh ngay", "sinh nam")):
            notes.append(tail)
    return "; ".join(dict.fromkeys(note for note in notes if note)) or None


def _is_participant_detail_line(text: str) -> bool:
    return fold_text(text).startswith(
        (
            "dia chi", "noi cu tru", "thuong tru", "noi o hien nay", "cung dia chi",
            "co mat", "vang mat", "co don xin vang mat", "quan he", "ghi chu",
        )
    )


def validate_defendant_entity(result: dict[str, Any]) -> dict[str, Any]:
    result.setdefault("warnings", [])
    full_name = str(result.get("full_name") or "")
    if full_name and any(term in fold_text(full_name) for term in DEFENDANT_BLOCKED_TERMS):
        result["full_name"] = None
        result["warnings"].append("defendant_name_forbidden_anchor")
    for field in SHORT_FIELDS:
        value = result.get(field)
        if isinstance(value, str) and len(value) > 80:
            result[field] = None
            result["warnings"].append(f"field_too_long:{field}")
    if not result.get("full_name"):
        result["warnings"].append("defendant_name_missing")
    split_reason = str(result.get("split_reason") or "")
    explicit_label = "defendant_label" in split_reason or "full_name_label" in split_reason
    has_identity_profile = explicit_label or any(
        result.get(field) not in (None, "") for field in DEFENDANT_IDENTITY_FIELDS
    )
    if result.get("full_name") and not has_identity_profile:
        result["warnings"].append("defendant_identity_profile_missing")
    result["entity_valid"] = bool(result.get("full_name") and has_identity_profile)
    result["warnings"] = list(dict.fromkeys(result["warnings"]))
    result["needs_review"] = bool(result["warnings"])
    return result


def validate_participant_entity(result: dict[str, Any]) -> dict[str, Any]:
    result.setdefault("warnings", [])
    if not result.get("role"):
        result["warnings"].append("participant_role_missing")
    if not result.get("full_name"):
        result["warnings"].append("participant_name_missing")
    result["warnings"] = list(dict.fromkeys(result["warnings"]))
    result["needs_review"] = bool(result["warnings"])
    return result


def _set(output: dict[str, Any], path: str, value: Any, line: dict[str, Any], confidence: float) -> None:
    if value in (None, ""):
        return
    group, field = path.split(".", 1)
    if output[group].get(field) not in (None, ""):
        return
    clean = str(value).strip(" :-.;")
    output[group][field] = clean
    evidence = {
        "field": path,
        "value": clean,
        "line_id": _line_id(line),
        "text": _text(line),
        "confidence": confidence,
        "source": "rule_anchor",
        "source_region": FRONT_PRE_CONTENT,
    }
    output["evidence"].append(evidence)
    output["field_meta"][path] = {
        "source": "rule_anchor",
        "source_region": FRONT_PRE_CONTENT,
        "confidence": confidence,
        "evidence_line_ids": [_line_id(line)],
    }


def _set_panel(output: dict[str, Any], field: str, value: str, line: dict[str, Any]) -> None:
    values = _split_panel_values(value) if field == "jurors" else [value]
    for clean in values:
        if not clean:
            continue
        if field == "jurors":
            if clean not in output["trial_panel"][field]:
                output["trial_panel"][field].append(clean)
        elif not output["trial_panel"][field]:
            output["trial_panel"][field] = clean
        else:
            continue
        output["evidence"].append(
            {
                "field": f"trial_panel.{field}", "value": clean, "line_id": _line_id(line),
                "text": _text(line), "confidence": 0.94, "source": "rule_anchor",
                "source_region": FRONT_PRE_CONTENT,
            }
        )


def _clean_panel_value(value: str, *, preserve_newlines: bool = False) -> str | None:
    value = re.sub(r"^[\s:;,.\-]+", "", value)
    if preserve_newlines:
        value = "\n".join(
            re.sub(r"[ \t]+", " ", line).strip(" ;,.-")
            for line in value.splitlines()
            if line.strip(" ;,.-")
        )
    else:
        value = re.sub(r"\s+", " ", value).strip(" ;,.-")
    return value or None


def _split_panel_values(value: str) -> list[str]:
    return [
        re.sub(r"^\s*\d+[.)]\s*", "", re.sub(r"\s+", " ", item)).strip()
        for item in re.split(r"[\n;]|,(?=\s*(?:Ông|Bà|[A-ZĐ]))", value)
        if item.strip()
    ]


def _number_after_anchor(text: str, anchor_pattern: str) -> str | None:
    number, _ = _number_and_tail_after_anchor(text, anchor_pattern)
    return number


def _number_and_tail_after_anchor(
    text: str,
    anchor_pattern: str,
) -> tuple[str | None, str | None]:
    anchor = re.search(anchor_pattern + r"\s*[:.]?\s*", text, re.I)
    if not anchor:
        return None, None
    number = CASE_NUMBER_TOKEN_RE.match(text, anchor.end())
    if not number:
        return None, text[anchor.end():]
    value = re.sub(r"\s*/\s*", "/", number.group(1)).strip(" .;,:")
    return value, text[number.end():]


def _text_after_anchor(text: str, anchor_pattern: str) -> str | None:
    anchor = re.search(anchor_pattern + r"\s*[:.]?\s*", text, re.I)
    return text[anchor.end():] if anchor else None


def _participant_represented_person(raw: str, role: str | None) -> str | None:
    if not role:
        return None
    first_line = raw.splitlines()[0] if raw.splitlines() else raw
    match = re.search(
        r"(?:của|cho)\s+(?:bị\s+cáo|bị\s+hại)\s+([^:：;]+)\s*[:：]",
        first_line,
        re.IGNORECASE,
    )
    return _clean_value(match.group(1)) if match else None


def _multi_person_names(primary_line: str | None) -> tuple[list[str], str | None]:
    if not primary_line:
        return [], None
    folded = fold_text(primary_line)
    if any(
        marker in folded
        for marker in ("dia chi", "noi cu tru", "cong ty", "van phong", "to chuc")
    ):
        return [], None
    starts = []
    for match in HONORIFIC_RE.finditer(primary_line):
        prefix = primary_line[:match.start()].rstrip().casefold()
        if not prefix or prefix.endswith((",", ";", " và")):
            starts.append(match.start())
    if len(starts) < 2:
        return [], None
    names: list[str] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(primary_line)
        segment = primary_line[start:end].strip(" ,;:-")
        name = _participant_name(segment)
        if name:
            names.append(name)
    notes = [_clean_value(value) for value in re.findall(r"\(([^)]+)\)", primary_line)]
    shared_note = "; ".join(dict.fromkeys(note for note in notes if note)) or None
    return list(dict.fromkeys(names)), shared_note


def _date_after_day_anchor(text: str) -> str | None:
    day = re.search(r"\bNgày\s*[:.]?\s*" + DATE_RE.pattern, text, re.I)
    return _normalize_date(day.group(1)) if day else None


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s*([-])\s*", r"\1", re.sub(r"\s*/\s*", "/", value))


def _clean_value(value: str | None) -> str | None:
    if not value:
        return None
    value = value.split("\n", 1)[0]
    value = value.split(";", 1)[0]
    value = re.sub(r"^[\s:;,./\-]+", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ,;:.-")
    return value or None


def _presence(value: str) -> str:
    folded = fold_text(value)
    if "co don xin vang mat" in folded:
        return "Có đơn xin vắng mặt"
    if "vang mat" in folded:
        return "Vắng mặt"
    return "Có mặt"


def _text(line: dict[str, Any]) -> str:
    return str(line.get("text") or "").strip()


def _line_id(line: dict[str, Any]) -> str:
    return str(line.get("line_id") or "")
