from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text
from court_ocr_extract.extractors.rule_parser import extract_identity_number, parse_vietnamese_date
from court_ocr_extract.final_excel_role_policy import (
    classify_final_role,
    normalized_row_identity,
)
from court_ocr_extract.final_excel_schema import FINAL_EXCEL_COLUMNS
from court_ocr_extract.source_region_policy import DECISION_TAIL, FRONT_PRE_CONTENT


CRIMINAL_FIRST_INSTANCE = "Hình sự sơ thẩm"


def build_final_excel_rows(extraction_result: Mapping[str, Any]) -> list[dict[str, str]]:
    metadata = _front_group(extraction_result, "metadata")
    trial_panel = _front_group(extraction_result, "trial_panel")
    common_notes: list[str] = []

    case_type = _final_case_type(extraction_result, metadata)
    if not case_type:
        common_notes.append("Không xác định chắc loại án")

    acceptance_number = _text(metadata.get("case_acceptance_number"))
    if not acceptance_number:
        common_notes.append("Thiếu số thụ lý")

    acceptance_date = _acceptance_date(extraction_result, metadata, acceptance_number)
    if not acceptance_date:
        common_notes.append("Thiếu ngày thụ lý")

    case_charges = _case_charges(extraction_result)
    defendant_charge_map = _defendant_charge_map(extraction_result, case_charges)
    decision_tail_status = _text(extraction_result.get("decision_tail_status"))

    presiding_judge = _text(trial_panel.get("presiding_judge"))
    if not presiding_judge:
        common_notes.append("Thiếu chủ tọa")

    output_warnings = _warning_strings(extraction_result.get("warnings"))
    if _contains_ocr_warning(output_warnings):
        common_notes.append("OCR nghi ngờ")
    if _contains_validator_rejection(output_warnings):
        common_notes.append("Field bị validator loại")

    entities: list[tuple[str, Mapping[str, Any], bool]] = [
        ("Bị cáo", _mapping(item), True)
        for item in _items(extraction_result.get("defendants"))
        if _mapping(item).get("entity_valid", True) is not False
        and _entity_is_front(_mapping(item))
    ]
    for item in _items(extraction_result.get("participants")):
        entity = _mapping(item)
        decision = classify_final_role(entity.get("role"))
        if decision.include_in_final and _entity_is_front(entity):
            entities.append((decision.normalized_role, entity, False))

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    case_id = _text(extraction_result.get("case_id"))
    for entity_index, (role, entity, is_defendant) in enumerate(entities):
        notes = list(common_notes)
        full_name = _text(entity.get("full_name"))
        identity = normalized_row_identity(case_id, full_name, role)
        if full_name and identity in seen:
            continue
        seen.add(identity if full_name else (*identity[:2], f"{identity[2]}:{entity_index}"))
        birth_year = _birth_year(entity.get("birth_date_or_year"))
        identity_number = _identity_number(entity)
        address = _entity_address(entity, defendant=is_defendant)
        legal_relationship, relationship_notes = _row_legal_relationship(
            role=role,
            entity=entity,
            entity_index=entity_index,
            is_defendant=is_defendant,
            criminal_case=case_type == CRIMINAL_FIRST_INSTANCE,
            case_charges=case_charges,
            defendant_charge_map=defendant_charge_map,
            decision_tail_status=decision_tail_status,
        )
        notes.extend(relationship_notes)

        if not role:
            notes.append("Thiếu tư cách tố tụng")
        if not full_name:
            notes.append("Thiếu họ tên")
        if not birth_year:
            notes.append("Thiếu năm sinh")
        if not identity_number:
            notes.append("Thiếu CCCD/CMND")
        if not address:
            notes.append("Thiếu địa chỉ")

        entity_warnings = _warning_strings(entity.get("warnings"))
        if _contains_ocr_warning(entity_warnings):
            notes.append("OCR nghi ngờ")
        if _contains_validator_rejection(entity_warnings):
            notes.append("Field bị validator loại")
        if bool(entity.get("needs_review")):
            notes.append("Người cần review")
        relationship_note = _text(
            entity.get("relationship_or_note") or entity.get("relationship")
        )
        if relationship_note:
            notes.append(relationship_note)
        evidence_line_ids = [
            str(value).strip()
            for value in _items(entity.get("evidence_line_ids"))
            if str(value).strip()
        ]
        if evidence_line_ids and (entity_warnings or bool(entity.get("needs_review"))):
            notes.append("evidence=" + ",".join(dict.fromkeys(evidence_line_ids)))

        rows.append(
            make_final_excel_row(
                {
                    "LOẠI ÁN": case_type,
                    "SỐ THỤ LÝ": acceptance_number,
                    "NGÀY THỤ LÝ (DD/MM/YYYY)": acceptance_date,
                    "QUAN HỆ PHÁP LUẬT": legal_relationship,
                    "TƯ CÁCH TỐ TỤNG": role,
                    "HỌ TÊN ĐƯƠNG SỰ": full_name,
                    "NĂM SINH": birth_year,
                    "CCCD": identity_number,
                    "ĐỊA CHỈ": address,
                    "HỌ TÊN CHỦ TỌA": presiding_judge,
                },
                notes=notes,
            )
        )
    return rows


def make_final_excel_row(
    values: Mapping[str, Any],
    *,
    notes: Iterable[str] = (),
) -> dict[str, str]:
    row = {column: _text(values.get(column)) for column in FINAL_EXCEL_COLUMNS}
    combined_notes = [
        *(_split_notes(row["GHI CHÚ"])),
        *(_text(note) for note in notes),
    ]
    row["GHI CHÚ"] = "; ".join(
        dict.fromkeys(note for note in combined_notes if note)
    )
    return row


def _final_case_type(
    extraction_result: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> str:
    document_type = _text(extraction_result.get("document_type"))
    metadata_case_type = _text(metadata.get("case_type"))
    judgment_number = _text(metadata.get("judgment_number"))
    if document_type == "judgment_criminal_first_instance":
        return CRIMINAL_FIRST_INSTANCE
    if fold_text(metadata_case_type) == "hinh su so tham":
        return CRIMINAL_FIRST_INSTANCE
    if re.search(r"(?:^|/)HS-?ST(?:$|[-/])", judgment_number, re.IGNORECASE):
        return CRIMINAL_FIRST_INSTANCE
    return ""


def _acceptance_date(
    extraction_result: Mapping[str, Any],
    metadata: Mapping[str, Any],
    acceptance_number: str,
) -> str:
    if not acceptance_number:
        return ""
    direct = parse_vietnamese_date(_text(metadata.get("case_acceptance_date")))
    if direct:
        return direct
    anchor = _mapping(extraction_result.get("anchor_segments"))
    for line in _items(anchor.get("metadata_lines")):
        text = _text(_mapping(line).get("text"))
        if "thu ly so" not in fold_text(text):
            continue
        date = _date_after_acceptance_number(text, acceptance_number)
        if date:
            return date
    for evidence in _items(extraction_result.get("evidence")):
        item = _mapping(evidence)
        if item.get("field") != "metadata.case_acceptance_number":
            continue
        date = _date_after_acceptance_number(_text(item.get("text")), acceptance_number)
        if date:
            return date
    return ""


def _date_after_acceptance_number(text: str, acceptance_number: str) -> str:
    if not acceptance_number:
        return ""
    normalized_text = re.sub(r"\s*/\s*", "/", text)
    if acceptance_number not in normalized_text:
        return ""
    tail = normalized_text.split(acceptance_number, 1)[1]
    return parse_vietnamese_date(tail) or ""


def _case_charges(extraction_result: Mapping[str, Any]) -> list[str]:
    charge_output = _mapping(extraction_result.get("charge_output"))
    evidence = [
        _mapping(item)
        for item in _items(charge_output.get("charge_evidence"))
        if _text(_mapping(item).get("source_region")) == DECISION_TAIL
    ]
    allowed_charge_keys = {
        _text(item.get("charge")).casefold()
        for item in evidence
        if _text(item.get("charge"))
    }
    if not allowed_charge_keys:
        return []
    charges = _items(extraction_result.get("case_charges")) or _items(
        charge_output.get("case_charges")
    )
    return list(
        dict.fromkeys(
            _text(value)
            for value in charges
            if _text(value).casefold() in allowed_charge_keys
        )
    )


def _defendant_charge_map(
    extraction_result: Mapping[str, Any],
    case_charges: list[str],
) -> Mapping[str, Any]:
    direct = _mapping(extraction_result.get("defendant_charge_map"))
    source = direct or _mapping(
        _mapping(extraction_result.get("charge_output")).get("defendant_charge_map")
    )
    allowed = {value.casefold() for value in case_charges}
    return {
        str(entity_id): [
            _text(value)
            for value in _items(values)
            if _text(value).casefold() in allowed
        ]
        for entity_id, values in source.items()
    }


def _front_group(
    extraction_result: Mapping[str, Any],
    group_name: str,
) -> dict[str, Any]:
    values = dict(_mapping(extraction_result.get(group_name)))
    if _text(values.get("source_region")) not in {"", FRONT_PRE_CONTENT}:
        return {}
    field_meta = _mapping(extraction_result.get("field_meta"))
    for field in list(values):
        meta = _mapping(field_meta.get(f"{group_name}.{field}"))
        region = _text(meta.get("source_region"))
        if region and region != FRONT_PRE_CONTENT:
            values[field] = None
    return values


def _entity_is_front(entity: Mapping[str, Any]) -> bool:
    return _text(entity.get("source_region")) in {"", FRONT_PRE_CONTENT}


def _row_legal_relationship(
    *,
    role: str,
    entity: Mapping[str, Any],
    entity_index: int,
    is_defendant: bool,
    criminal_case: bool,
    case_charges: list[str],
    defendant_charge_map: Mapping[str, Any],
    decision_tail_status: str,
) -> tuple[str, list[str]]:
    if not criminal_case:
        return "", ["Không xác định chắc quan hệ pháp luật"]

    notes: list[str] = []
    if decision_tail_status == "heading_not_found":
        notes.append(
            "Không tìm thấy phần Quyết định trong phạm vi OCR cuối văn bản"
        )

    defendant_specific = is_defendant or fold_text(role) in {
        "bi cao",
        "phap nhan thuong mai bi cao",
    }
    if defendant_specific:
        entity_id = _text(
            entity.get("entity_id")
            or entity.get("source_block_id")
            or f"defendant_{entity_index + 1:03d}"
        )
        charges = [
            _text(value)
            for value in _items(defendant_charge_map.get(entity_id))
            if _text(value)
        ]
        if charges:
            return "; ".join(dict.fromkeys(charges)), notes
        notes.append(
            "Chưa gắn chắc tội danh với bị cáo từ phần Quyết định"
        )
        return "", notes

    if case_charges:
        return "; ".join(case_charges), notes
    notes.append("Chưa trích xuất được tội danh từ phần Quyết định")
    return "", notes


def _birth_year(value: Any) -> str:
    years = re.findall(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", _text(value))
    return years[-1] if years else ""


def _identity_number(entity: Mapping[str, Any]) -> str:
    direct = _text(entity.get("cccd") or entity.get("id_number"))
    if re.fullmatch(r"\d{9,12}", direct):
        return direct
    raw = _text(entity.get("raw_block") or entity.get("raw_text"))
    return extract_identity_number(raw) or ""


def _entity_address(entity: Mapping[str, Any], *, defendant: bool) -> str:
    if defendant:
        value = entity.get("current_address") or entity.get("permanent_address")
    else:
        value = entity.get("address")
    address = re.sub(
        r"^\s*hiện\s+tại\s*[:：]\s*",
        "",
        _text(value),
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", address).strip(" ;,.")


def _contains_ocr_warning(warnings: list[str]) -> bool:
    return any(
        "ocr" in warning.casefold() or "low_confidence" in warning.casefold()
        for warning in warnings
    )


def _contains_validator_rejection(warnings: list[str]) -> bool:
    markers = ("field_too_long", "forbidden", "invalid", "validator", "rejected")
    return any(any(marker in warning.casefold() for marker in markers) for warning in warnings)


def _warning_strings(value: Any) -> list[str]:
    return [_text(item) for item in _items(value) if isinstance(item, str) and _text(item)]


def _split_notes(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _items(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _text(value: Any) -> str:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip(" ;")
