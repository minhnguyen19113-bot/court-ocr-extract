from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text
from court_ocr_extract.final_excel_role_policy import (
    classify_final_role,
    normalized_row_identity,
)
from court_ocr_extract.source_region_policy import FRONT_PRE_CONTENT


OTHER_PARTICIPANTS_SHEET_NAME = "NGUOI_THAM_GIA_KHAC"
OTHER_PARTICIPANT_COLUMNS = [
    "LOẠI ÁN",
    "SỐ THỤ LÝ",
    "TƯ CÁCH TỐ TỤNG",
    "HỌ TÊN",
    "NGƯỜI ĐƯỢC ĐẠI DIỆN/BẢO VỆ",
    "ĐỊA CHỈ",
    "TÌNH TRẠNG THAM GIA",
    "GHI CHÚ",
]


def build_other_participant_rows(
    extraction_result: Mapping[str, Any],
) -> list[dict[str, str]]:
    metadata = _mapping(extraction_result.get("metadata"))
    case_id = _text(extraction_result.get("case_id"))
    case_type = _case_type(extraction_result, metadata)
    acceptance_number = _text(metadata.get("case_acceptance_number"))
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for index, raw in enumerate(_items(extraction_result.get("participants"))):
        entity = _mapping(raw)
        if _text(entity.get("source_region")) not in {"", FRONT_PRE_CONTENT}:
            continue
        role = _text(entity.get("role"))
        decision = classify_final_role(role)
        if not decision.include_in_other:
            continue
        full_name = _text(entity.get("full_name"))
        identity = normalized_row_identity(case_id, full_name, decision.normalized_role)
        if full_name and identity in seen:
            continue
        seen.add(identity if full_name else (*identity[:2], f"{identity[2]}:{index}"))

        notes = [
            _text(entity.get("relationship_or_note") or entity.get("relationship")),
        ]
        if decision.category == "other_unclassified":
            notes.append("Tư cách cần review")
        if not role:
            notes.append("Thiếu tư cách tố tụng")
        if not full_name:
            notes.append("Thiếu họ tên")
        if bool(entity.get("needs_review")):
            notes.append("Người cần review")
        notes.extend(_warning_strings(entity.get("warnings")))

        rows.append(
            make_other_participant_row(
                {
                    "LOẠI ÁN": case_type,
                    "SỐ THỤ LÝ": acceptance_number,
                    "TƯ CÁCH TỐ TỤNG": role or decision.normalized_role,
                    "HỌ TÊN": full_name,
                    "NGƯỜI ĐƯỢC ĐẠI DIỆN/BẢO VỆ": entity.get("represented_person"),
                    "ĐỊA CHỈ": entity.get("address"),
                    "TÌNH TRẠNG THAM GIA": entity.get("presence_status"),
                },
                notes=notes,
            )
        )
    return rows


def make_other_participant_row(
    values: Mapping[str, Any],
    *,
    notes: Iterable[object] = (),
) -> dict[str, str]:
    row = {column: _text(values.get(column)) for column in OTHER_PARTICIPANT_COLUMNS}
    row["ĐỊA CHỈ"] = re.sub(
        r"^\s*hiện\s+tại\s*[:：]\s*",
        "",
        row["ĐỊA CHỈ"],
        flags=re.IGNORECASE,
    ).strip(" ;,.")
    combined = [
        *[item.strip() for item in row["GHI CHÚ"].split(";") if item.strip()],
        *(_text(note) for note in notes),
    ]
    row["GHI CHÚ"] = "; ".join(dict.fromkeys(item for item in combined if item))
    return row


def _case_type(
    extraction_result: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> str:
    document_type = _text(extraction_result.get("document_type"))
    explicit = _text(metadata.get("case_type"))
    judgment_number = _text(metadata.get("judgment_number"))
    if document_type == "judgment_criminal_first_instance":
        return "Hình sự sơ thẩm"
    if fold_text(explicit) == "hinh su so tham":
        return "Hình sự sơ thẩm"
    if re.search(r"(?:^|/)HS-?ST(?:$|[-/])", judgment_number, re.IGNORECASE):
        return "Hình sự sơ thẩm"
    return explicit


def _warning_strings(value: Any) -> list[str]:
    return [_text(item) for item in _items(value) if isinstance(item, str) and _text(item)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _items(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _text(value: Any) -> str:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip(" ;")
