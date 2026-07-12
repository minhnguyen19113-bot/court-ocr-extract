from __future__ import annotations

import re
import unicodedata
from typing import Any

from court_ocr_extract.extractors.pre_content_schema import empty_pre_content_output


PARTICIPANT_ROLES = {
    "bi hai": "Bị hại",
    "nguoi bi hai": "Người bị hại",
    "nguoi giam ho": "Người giám hộ",
    "nguoi bao chua": "Người bào chữa",
    "nguoi bao ve quyen va loi ich hop phap": "Người bảo vệ quyền và lợi ích hợp pháp",
    "nguoi co quyen loi, nghia vu lien quan": "Người có quyền lợi, nghĩa vụ liên quan",
}


def extract_pre_content_rules(segment: dict[str, Any]) -> dict[str, Any]:
    document_type = str(segment.get("document_type") or "unknown")
    lines = [dict(line) for line in segment.get("pre_content_lines", [])]
    if document_type == "correction_notice":
        return _extract_correction_notice(lines)
    output = empty_pre_content_output(document_type)
    _extract_metadata(lines, output)
    _extract_trial_panel(lines, output)
    output["defendants"] = _extract_defendants(lines)
    output["participants"] = _extract_participants(lines)
    output["warnings"].extend(segment.get("warnings", []))
    if document_type == "unknown":
        output["warnings"].append("rule_extraction_on_unknown_document_type")
    if not output["defendants"]:
        output["warnings"].append("defendant_block_not_found")
    missing = [path for path in ("metadata.judgment_number", "trial_panel.presiding_judge") if not _get_path(output, path)]
    output["warnings"].extend(f"missing:{path}" for path in missing)
    output["needs_review"] = bool(output["warnings"] or any(item["needs_review"] for item in output["defendants"] + output["participants"]))
    return output


def _extract_metadata(lines: list[dict[str, Any]], output: dict[str, Any]) -> None:
    for index, line in enumerate(lines):
        text = _text(line)
        folded = _fold(text)
        if not output["metadata"]["court_name"] and "toa an nhan dan" in folded:
            value = text
            if index + 1 < len(lines) and len(_text(lines[index + 1])) < 100:
                value += " " + _text(lines[index + 1])
            _set(output, "metadata.court_name", value, line, 0.92)
        match = re.search(r"b[aả]n\s*[aá]n\s*(?:s[oố])?\s*[:.]?\s*([^\s,;]+)", text, re.I)
        if match:
            _set(output, "metadata.judgment_number", match.group(1), line, 0.96)
        match = re.search(r"ng[aà]y\s*[:.]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.I)
        if match:
            _set(output, "metadata.judgment_date", match.group(1), line, 0.92)
        if "thu ly so" in folded:
            _set(output, "metadata.case_acceptance_number", _after_anchor(text, "số"), line, 0.88)
        if "quyet dinh dua vu an ra xet xu so" in folded:
            _set(output, "metadata.trial_decision_number", _after_anchor(text, "số"), line, 0.90)
        if "quyet dinh hoan phien toa so" in folded:
            _set(output, "metadata.postponement_decision_number", _after_anchor(text, "số"), line, 0.90)
        if "xet xu" in folded and ("ngay" in folded or "tai" in folded) and not output["metadata"]["trial_location_or_date_sentence"]:
            _set(output, "metadata.trial_location_or_date_sentence", text, line, 0.70)
    number = output["metadata"]["judgment_number"] or ""
    if "hs" in str(number).lower():
        output["metadata"]["case_type"] = "Hình sự sơ thẩm"


def _extract_trial_panel(lines: list[dict[str, Any]], output: dict[str, Any]) -> None:
    anchors = {
        "chu toa phien toa": "presiding_judge",
        "tham phan": "presiding_judge",
        "cac hoi tham nhan dan": "jurors",
        "hoi tham nhan dan": "jurors",
        "thu ky phien toa": "clerk",
        "dai dien vien kiem sat": "prosecutor",
    }
    active_jurors = False
    for index, line in enumerate(lines):
        text = _text(line)
        folded = _fold(text)
        matched = next(((anchor, field) for anchor, field in anchors.items() if anchor in folded), None)
        if matched:
            anchor, field = matched
            value = _value_after_colon(text)
            if field != "jurors" and not value and index + 1 < len(lines):
                value = _numbered_value(_text(lines[index + 1]))
            if field == "jurors":
                active_jurors = True
                if value:
                    output["trial_panel"][field].append(value)
                    _evidence(output, f"trial_panel.{field}", line, value, 0.84)
            elif value:
                _set(output, f"trial_panel.{field}", value, line, 0.88)
            continue
        if active_jurors:
            if re.match(r"^\s*\d+[.)]\s*", text):
                value = _numbered_value(text)
                output["trial_panel"]["jurors"].append(value)
                _evidence(output, "trial_panel.jurors", line, value, 0.78)
            elif folded:
                active_jurors = False


def _extract_defendants(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = next((i for i, line in enumerate(lines) if re.search(r"(?:doi voi )?bi cao\s*:", _fold(_text(line)))), None)
    numbered = [i for i, line in enumerate(lines) if _is_defendant_start(_text(line))]
    if start is None and numbered:
        start = numbered[0]
    if start is None:
        return []
    stop = next((i for i in range(start + 1, len(lines)) if _is_participant_heading(_text(lines[i]))), len(lines))
    starts = [i for i in numbered if start <= i < stop]
    if not starts:
        starts = [start]
    elif start < starts[0] and _value_after_colon(_text(lines[start])):
        starts.insert(0, start)
    blocks = []
    for position, block_start in enumerate(starts):
        block_end = starts[position + 1] if position + 1 < len(starts) else stop
        block_lines = lines[block_start:block_end]
        blocks.append(_parse_defendant_block(block_lines))
    return blocks


def _parse_defendant_block(lines: list[dict[str, Any]]) -> dict[str, Any]:
    result = {field: None for field in (
        "full_name", "alias", "birth_date_or_year", "birth_place", "gender", "nationality",
        "ethnicity", "religion", "education", "occupation", "permanent_address", "current_address",
        "father_name", "mother_name", "spouse", "children", "criminal_record", "detention_status", "presence_status",
    )}
    result.update({
        "raw_block": "\n".join(_text(line) for line in lines),
        "evidence_line_ids": [_line_id(line) for line in lines],
        "needs_review": False,
        "warnings": [],
    })
    mappings = {
        "ho va ten": "full_name", "bi cao": "full_name", "ten goi khac": "alias",
        "sinh ngay": "birth_date_or_year", "sinh nam": "birth_date_or_year", "noi sinh": "birth_place",
        "gioi tinh": "gender", "quoc tich": "nationality", "dan toc": "ethnicity",
        "ton giao": "religion", "trinh do hoc van": "education", "nghe nghiep": "occupation",
        "noi thuong tru": "permanent_address", "dia chi thuong tru": "permanent_address",
        "cho o hien nay": "current_address", "cha": "father_name", "me": "mother_name",
        "vo": "spouse", "chong": "spouse", "con": "children", "tien an": "criminal_record",
    }
    for line in lines:
        text = _text(line)
        folded = _fold(text)
        for anchor, field in mappings.items():
            if anchor in folded and not result[field]:
                value = _value_after_colon(text)
                if field == "full_name" and not value:
                    value = re.sub(r"^\s*\d+[.)]\s*", "", text).strip()
                result[field] = value or None
        if "tam giam" in folded or "tam giu" in folded:
            result["detention_status"] = text
        if "co mat" in folded or "vang mat" in folded:
            result["presence_status"] = text
    if not result["full_name"]:
        first = _text(lines[0]) if lines else ""
        candidate = re.sub(r"^\s*\d+[.)]\s*", "", first).strip()
        candidate = re.sub(r"^(?:h[oọ]\s+v[aà]\s+t[eê]n|b[iị]\s+c[aá]o)\s*:\s*", "", candidate, flags=re.I)
        result["full_name"] = candidate or None
    if not result["full_name"]:
        result["warnings"].append("defendant_name_missing")
        result["needs_review"] = True
    return result


def _extract_participants(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    participants = []
    current_role = None
    for index, line in enumerate(lines):
        text = _text(line)
        folded = _fold(text)
        role = next((label for anchor, label in PARTICIPANT_ROLES.items() if anchor in folded), None)
        if role:
            current_role = role
            value = _value_after_colon(text)
            if value:
                participants.append(_participant(role, value, [line]))
            continue
        if current_role and re.match(r"^\s*\d+[.)]\s*", text):
            block = [line]
            if index + 1 < len(lines) and "dia chi" in _fold(_text(lines[index + 1])):
                block.append(lines[index + 1])
            participants.append(_participant(current_role, _numbered_value(text), block))
    return participants


def _participant(role: str, value: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    name = re.split(r"[,;]", value, maxsplit=1)[0].strip()
    return {
        "role": role, "full_name": name or None, "birth_date_or_year": None,
        "address": next((_value_after_colon(_text(line)) for line in lines if "dia chi" in _fold(_text(line))), None),
        "presence_status": next((_text(line) for line in lines if "co mat" in _fold(_text(line)) or "vang mat" in _fold(_text(line))), None),
        "relationship": None, "raw_block": "\n".join(_text(line) for line in lines),
        "evidence_line_ids": [_line_id(line) for line in lines], "needs_review": not bool(name), "warnings": [],
    }


def _extract_correction_notice(lines: list[dict[str, Any]]) -> dict[str, Any]:
    output = empty_pre_content_output("correction_notice")
    output["notice"] = {key: None for key in (
        "notice_number", "notice_date", "referenced_judgment_number", "correction_from", "correction_to"
    )}
    for line in lines:
        text, folded = _text(line), _fold(_text(line))
        if "thong bao so" in folded:
            output["notice"]["notice_number"] = _after_anchor(text, "số")
        if not output["notice"]["notice_date"]:
            match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
            if match:
                output["notice"]["notice_date"] = match.group(1)
        if "ban an so" in folded:
            output["notice"]["referenced_judgment_number"] = _after_anchor(text, "số")
        if "tu:" in folded or "tu “" in folded:
            output["notice"]["correction_from"] = _value_after_colon(text)
        if "thanh:" in folded or "thanh “" in folded:
            output["notice"]["correction_to"] = _value_after_colon(text)
    output["warnings"] = ["correction_notice_excluded_from_judgment_benchmark"]
    output["needs_review"] = True
    return output


def _is_defendant_start(text: str) -> bool:
    folded = _fold(text)
    return bool(re.match(r"^\d+[.)]\s*(?:ho va ten\s*:|[a-z])", folded) or re.match(r"^ho va ten\s*:", folded))


def _is_participant_heading(text: str) -> bool:
    folded = _fold(text)
    return any(anchor in folded for anchor in PARTICIPANT_ROLES) or "nhung nguoi tham gia to tung" in folded


def _set(output: dict[str, Any], path: str, value: Any, line: dict[str, Any], confidence: float) -> None:
    if value in (None, ""):
        return
    group, field = path.split(".", 1)
    if output[group].get(field) in (None, ""):
        output[group][field] = str(value).strip(" :-")
        _evidence(output, path, line, output[group][field], confidence)


def _evidence(output: dict[str, Any], path: str, line: dict[str, Any], value: Any, confidence: float) -> None:
    item = {"field": path, "value": value, "line_id": _line_id(line), "text": _text(line), "confidence": confidence, "source": "rule"}
    output["evidence"].append(item)
    output["field_meta"][path] = {"confidence": confidence, "source": "rule", "evidence_line_ids": [_line_id(line)]}


def _get_path(output: dict[str, Any], path: str) -> Any:
    group, field = path.split(".", 1)
    return output[group].get(field)


def _after_anchor(text: str, anchor: str) -> str | None:
    match = re.search(re.escape(anchor) + r"\s*[:.]?\s*(.+)$", text, re.I)
    return match.group(1).strip() if match else _value_after_colon(text)


def _value_after_colon(text: str) -> str | None:
    parts = re.split(r"[:：]", text, maxsplit=1)
    return parts[1].strip(" -") if len(parts) == 2 and parts[1].strip(" -") else None


def _numbered_value(text: str) -> str:
    return re.sub(r"^\s*\d+[.)]\s*", "", text).strip()


def _text(line: dict[str, Any]) -> str:
    return str(line.get("text") or "").strip()


def _line_id(line: dict[str, Any]) -> str:
    return str(line.get("line_id") or "")


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    return re.sub(r"\s+", " ", "".join(char for char in value if unicodedata.category(char) != "Mn")).strip()
