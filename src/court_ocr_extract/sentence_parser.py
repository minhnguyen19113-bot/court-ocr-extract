from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from court_ocr_extract.charge_parser import (
    iter_verdict_blocks,
    match_defendant_entities,
    parse_verdict_candidate,
)
from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text
from court_ocr_extract.extractors.rule_parser import parse_vietnamese_date
from court_ocr_extract.source_region_policy import DECISION_TAIL


PRIMARY_PENALTY_KINDS = {
    "term_imprisonment",
    "life_imprisonment",
    "death_penalty",
    "suspended_imprisonment",
    "non_custodial_reform",
    "fine",
    "warning",
    "expulsion",
    "exemption",
    "unknown",
}

_DURATION_PART = (
    r"\d{1,3}(?:\s*\([^()\n]{1,40}\))?\s*(?:năm|tháng|ngày)"
)
_DURATION_SEQUENCE = rf"{_DURATION_PART}(?:(?:\s*,\s*|\s+){_DURATION_PART}){{0,2}}"
_DURATION_COMPONENT_RE = re.compile(
    r"(?P<value>\d{1,3})(?:\s*\([^()\n]{1,40}\))?\s*"
    r"(?P<unit>năm|tháng|ngày)",
    re.I,
)
_TERM_RE = re.compile(rf"(?P<duration>{_DURATION_SEQUENCE})\s+tù\b", re.I)
_SUSPENDED_RE = re.compile(r"(?:cho|được)\s+hưởng\s+án\s+treo", re.I)
_PROBATION_RE = re.compile(
    rf"thời\s+gian\s+thử\s+thách(?:\s+là)?\s+(?P<duration>{_DURATION_SEQUENCE})",
    re.I,
)
_NON_CUSTODIAL_RE = re.compile(
    rf"(?:(?P<before>{_DURATION_SEQUENCE})\s+cải\s+tạo\s+không\s+giam\s+giữ"
    rf"|cải\s+tạo\s+không\s+giam\s+giữ\s+(?P<after>{_DURATION_SEQUENCE}))",
    re.I,
)
_MONEY_RE = re.compile(
    r"(?:hình\s+phạt\s+chính\s+là\s+)?phạt(?:\s+bị\s+cáo[^\d\n]{0,100})?"
    r"(?:\s+tiền)?\s*(?:số\s+tiền\s*)?(?P<amount>\d[\d. ,]{2,20})\s*đồng",
    re.I,
)
_AGGREGATE_RE = re.compile(
    rf"(?:hình\s+phạt\s+chung(?:\s+là)?|phải\s+chấp\s+hành\s+hình\s+phạt\s+chung\s+là)"
    rf"\s*[:：]?\s*(?P<penalty>{_DURATION_SEQUENCE}\s+tù|tù\s+chung\s+thân|tử\s+hình)",
    re.I,
)
_ADDITIONAL_ANCHOR_RE = re.compile(
    r"(?:hình\s+ph(?:ạt|át)\s+bổ\s+sung|ph(?:ạt|át)\s+bổ\s+sung)",
    re.I,
)
_DATE_VALUE = (
    r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{4}|"
    r"\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})"
)
_START_RE = re.compile(
    r"thời\s+hạn\s+tù(?:\s+được)?\s+tính\s+từ\s+ngày\s+"
    rf"(?P<value>{_DATE_VALUE}|"
    r"bắt(?:\s+bị\s+cáo)?\s+chấp\s+hành\s+án|"
    r"(?:bắt\s+giam|bất\s+giam|bắt\s+giảm)\s+bị\s+cáo\s+để\s+thi\s+hành\s+án)",
    re.I,
)
_PROBATION_START_RE = re.compile(
    rf"(?P<value>tính\s+từ\s+ngày\s+tuyên\s+án"
    rf"(?:\s+sơ\s+thẩm)?(?:\s*\((?P<date>{_DATE_VALUE})\))?)",
    re.I,
)
_DETENTION_CREDIT_RE = re.compile(
    rf"(?:được\s+)?trừ\s+(?:ngày|thời\s+gian)(?:\s+đã)?\s+tạm\s+giữ"
    rf"(?:\s*,?\s*tạm\s+giam)?(?:\s+từ\s+(?:ngày\s+)?(?P<from>{_DATE_VALUE})"
    rf"\s+đến\s+(?:ngày\s+)?(?P<to>{_DATE_VALUE}))?",
    re.I,
)
_COMPLETION_PATTERNS = (
    re.compile(r"đã\s+chấp\s+hành\s+xong\s+hình\s+ph(?:ạt|át)\s+tù", re.I),
    re.compile(r"thời\s+hạn\s+tù\s+bằng(?:\s+với)?\s+thời\s+gian\s+tạm\s+giam", re.I),
)
_RELEASE_RE = re.compile(
    r"(?:tuyên\s+bố\s+)?trả\s+tự\s+do(?:\s+ngay)?\s+tại\s+phiên\s+tòa"
    r"|(?:tuyên\s+bố\s+)?trả\s+tự\s+do(?:\s+ngay)?\s+cho\s+bị\s+cáo[^.\n]{0,100}"
    r"\s+tại\s+phiên\s+tòa",
    re.I,
)
_CIVIL_MONEY_MARKERS = (
    "an phi",
    "boi thuong",
    "tra lai tien",
    "nop lai tien",
    "truy thu",
    "sung cong",
    "tien goc",
    "tien lai",
    "nghia vu dan su",
)
_UNRESOLVED_COLLECTIVE_MARKERS = (
    "cac bi cao con lai",
    "nhung bi cao khac",
    "cac bi cao neu tren",
    "nhung bi cao con lai",
)
_SENTENCE_SECTION_BOUNDARIES = (
    "xu ly vat chung",
    "bien phap tu phap",
    "an phi",
    "quyen khang cao",
    "noi nhan",
)
SENTENCE_COMPLETENESS_WARNINGS = {
    "sentence_start_anchor_unparsed",
    "probation_duration_partial",
    "probation_start_unparsed",
    "detention_credit_anchor_unparsed",
    "completion_anchor_unparsed",
    "additional_penalty_anchor_unparsed",
    "sentence_evidence_span_inconsistent",
}


def parse_defendant_sentences(
    lines_or_text: str | Iterable[Mapping[str, Any]],
    *,
    defendants: Iterable[Mapping[str, Any]] = (),
    source_region: str = DECISION_TAIL,
    min_name_match_score: float = 88.0,
    name_match_ambiguity_gap: float = 5.0,
) -> dict[str, Any]:
    if source_region != DECISION_TAIL:
        return _empty_output(f"sentence_source_region_not_allowed:{source_region}")

    defendant_list = [dict(item) for item in defendants if isinstance(item, Mapping)]
    decision_input, source_warnings = _decision_only_input(lines_or_text)
    blocks = iter_verdict_blocks(decision_input)
    sentence_map: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    warnings = list(source_warnings)
    invalid_count = 0
    parsed_count = 0

    for original_block in blocks:
        block = _trim_sentence_block(original_block)
        if not block.get("raw_text"):
            continue
        parsed_verdict = parse_verdict_candidate(
            block,
            defendant_list,
            min_name_match_score=min_name_match_score,
            name_match_ambiguity_gap=name_match_ambiguity_gap,
        )
        raw_text = str(block.get("raw_text") or "").strip()
        entity_ids = list(parsed_verdict.defendant_entity_ids)
        entity_names = list(parsed_verdict.defendant_names)
        match_method = parsed_verdict.match_method
        match_warning = parsed_verdict.warning if not entity_ids else ""
        if not entity_ids:
            matched = match_defendant_entities(
                raw_text,
                defendant_list,
                min_name_match_score=min_name_match_score,
                name_match_ambiguity_gap=name_match_ambiguity_gap,
            )
            entity_ids = list(matched["defendant_entity_ids"])
            entity_names = list(matched["defendant_names"])
            match_method = str(matched["match_method"])
            match_warning = str(matched["warning"])

        if any(marker in fold_text(raw_text) for marker in _UNRESOLVED_COLLECTIVE_MARKERS):
            entity_ids = []
            warnings.append("unresolved_collective_defendant_sentence_mapping")
        elif not entity_ids:
            warnings.append(_sentence_mapping_warning(match_warning))

        base = _parse_sentence_fields(raw_text)
        completeness_warnings = _sentence_completeness_warnings(raw_text, base)
        warnings.extend(completeness_warnings)
        if not base["primary_penalty_text"]:
            invalid_count += 1
            warnings.extend(
                [
                    "sentence_candidate_found_but_not_parsed",
                    "sentence_duration_missing",
                    "invalid_sentence_candidate_rejected",
                ]
            )
            continue

        per_entity = _split_distinct_entity_sentences(
            raw_text,
            entity_ids,
            defendant_list,
        )
        records = per_entity or {entity_id: dict(base) for entity_id in entity_ids}
        if len(entity_ids) > 1 and not per_entity and "moi bi cao" not in fold_text(raw_text):
            warnings.append("ambiguous_defendant_sentence_mapping")
            records = {}

        for entity_id, fields in records.items():
            names = [_defendant_name(entity_id, defendant_list)]
            line_ids = [
                str(value) for value in block.get("line_ids", []) if str(value)
            ]
            record_warnings = list(completeness_warnings)
            if not _evidence_span_is_consistent(raw_text, line_ids):
                record_warnings.append("sentence_evidence_span_inconsistent")
                warnings.append("sentence_evidence_span_inconsistent")
            record = _sentence_record(
                fields,
                defendant_entity_ids=[entity_id],
                defendant_names=[name for name in names if name],
                source_region=DECISION_TAIL,
                page_number=_optional_int(block.get("page_number")),
                line_ids=line_ids,
                raw_text=raw_text,
                match_method=match_method,
                confidence="high" if entity_id in entity_ids else "medium",
                warnings=record_warnings,
            )
            _merge_sentence(sentence_map, entity_id, record, warnings)
            evidence.append(record)
            parsed_count += 1

    _apply_follow_on_details(
        decision_input,
        defendant_list,
        sentence_map,
        evidence,
        warnings,
        min_name_match_score=min_name_match_score,
        name_match_ambiguity_gap=name_match_ambiguity_gap,
    )

    for record in sentence_map.values():
        record["display_text"] = format_sentence_for_excel(record)

    mapped_count = len(sentence_map)
    if mapped_count < len(defendant_list):
        warnings.append(f"sentence_coverage_incomplete:{mapped_count}/{len(defendant_list)}")
    diagnostics = {
        "sentence_candidate_count": len(blocks),
        "parsed_sentence_count": parsed_count,
        "mapped_defendant_sentence_count": mapped_count,
        "unmapped_sentence_count": max(0, len(blocks) - parsed_count),
        "invalid_sentence_count": invalid_count,
        "suspended_sentence_count": sum(
            bool(item.get("suspended")) for item in sentence_map.values()
        ),
        "aggregate_sentence_count": sum(
            bool(item.get("is_aggregate")) for item in sentence_map.values()
        ),
        "additional_penalty_count": sum(
            len(item.get("additional_penalties", [])) for item in sentence_map.values()
        ),
    }
    return {
        "defendant_sentence_map": sentence_map,
        "sentence_evidence": evidence,
        "warnings": list(dict.fromkeys(item for item in warnings if item)),
        "diagnostics": diagnostics,
    }


def empty_sentence_output(warning: str = "") -> dict[str, Any]:
    return _empty_output(warning)


def format_sentence_for_excel(sentence: Mapping[str, Any]) -> str:
    primary = _text(sentence.get("aggregate_penalty_text")) or _text(
        sentence.get("primary_penalty_text")
    )
    parts = [primary] if primary else []
    probation = _text(sentence.get("probation_text"))
    probation_start = _text(sentence.get("probation_start_text"))
    if sentence.get("suspended") and primary and "án treo" not in fold_text(primary):
        parts[0] = f"{primary}, cho hưởng án treo"
    if probation:
        parts.append(
            f"{probation}, {probation_start}" if probation_start else probation
        )
    for key in (
        "sentence_start_text",
        "detention_credit_text",
        "completion_text",
        "release_text",
    ):
        value = _text(sentence.get(key))
        if value:
            parts.append(value)
    additional = [_text(value) for value in sentence.get("additional_penalties", [])]
    additional = [value for value in additional if value]
    if additional:
        parts.append("hình phạt bổ sung: " + "; ".join(dict.fromkeys(additional)))
    return "; ".join(dict.fromkeys(part for part in parts if part))


def _parse_sentence_fields(raw_text: str) -> dict[str, Any]:
    fields = _blank_sentence_fields()
    folded = fold_text(raw_text)

    aggregate = _AGGREGATE_RE.search(raw_text)
    if aggregate:
        fields["aggregate_penalty_text"] = (
            "Hình phạt chung: " + _normalize_penalty_text(aggregate.group("penalty"))
        )
        fields["is_aggregate"] = True

    suspended = bool(_SUSPENDED_RE.search(raw_text))
    term = _TERM_RE.search(raw_text)
    non_custodial = _NON_CUSTODIAL_RE.search(raw_text)
    if re.search(r"\btù\s+chung\s+thân\b", raw_text, re.I):
        fields.update(primary_penalty_kind="life_imprisonment", primary_penalty_text="Tù chung thân")
    elif re.search(r"\btử\s+hình\b", raw_text, re.I):
        fields.update(primary_penalty_kind="death_penalty", primary_penalty_text="Tử hình")
    elif non_custodial:
        duration = non_custodial.group("before") or non_custodial.group("after")
        _set_duration(fields, duration)
        fields.update(
            primary_penalty_kind="non_custodial_reform",
            primary_penalty_text=f"{_format_duration(duration)} cải tạo không giam giữ",
        )
    elif suspended:
        duration = term.group("duration") if term else _duration_before(raw_text, _SUSPENDED_RE.search(raw_text).start())
        if duration:
            _set_duration(fields, duration)
            fields.update(
                primary_penalty_kind="suspended_imprisonment",
                primary_penalty_text=f"{_format_duration(duration)} tù",
                suspended=True,
                execution_status="suspended",
            )
    elif term:
        duration = term.group("duration")
        _set_duration(fields, duration)
        fields.update(
            primary_penalty_kind="term_imprisonment",
            primary_penalty_text=f"{_format_duration(duration)} tù",
            execution_status="custodial",
        )
    else:
        fine = _primary_fine_match(raw_text)
        if fine:
            amount = re.sub(r"\s+", "", fine.group("amount")).strip(".,")
            fields.update(primary_penalty_kind="fine", primary_penalty_text=f"Phạt tiền {amount} đồng")
        elif re.search(r"\bmiễn\s+hình\s+phạt\b", raw_text, re.I):
            fields.update(primary_penalty_kind="exemption", primary_penalty_text="Miễn hình phạt")
        elif re.search(r"\bcảnh\s+cáo\b", raw_text, re.I):
            fields.update(primary_penalty_kind="warning", primary_penalty_text="Cảnh cáo")
        elif re.search(r"\btrục\s+xuất\b", raw_text, re.I):
            fields.update(primary_penalty_kind="expulsion", primary_penalty_text="Trục xuất")

    probation = _PROBATION_RE.search(raw_text)
    if probation:
        duration = probation.group("duration")
        values = _duration_values(duration)
        fields.update(
            probation_duration_years=values["years"],
            probation_duration_months=values["months"],
            probation_duration_days=values["days"],
            probation_text=f"thời gian thử thách {_format_duration(duration)}",
        )

    probation_start = _PROBATION_START_RE.search(raw_text)
    if probation_start:
        value = "tính từ ngày tuyên án"
        if "so tham" in fold_text(probation_start.group("value")):
            value += " sơ thẩm"
        explicit_date = probation_start.group("date")
        if explicit_date:
            parsed_date = _parse_date_value(explicit_date)
            if parsed_date:
                value += f" {parsed_date}"
        fields["probation_start_text"] = value

    start = _START_RE.search(raw_text)
    if start:
        value = start.group("value")
        parsed_date = _parse_date_value(value)
        normalized = parsed_date or re.sub(r"\s+", " ", value).strip()
        folded_value = fold_text(normalized)
        if "bat giam bi cao" in folded_value and "de thi hanh an" in folded_value:
            normalized = "bắt giam bị cáo để thi hành án"
        else:
            normalized = re.sub(
                r"^bắt\s+bị\s+cáo\s+", "bắt ", normalized, flags=re.I
            )
        fields["sentence_start_text"] = f"thời hạn tù tính từ ngày {normalized}"

    credit = _DETENTION_CREDIT_RE.search(raw_text)
    if credit:
        credit_text = "được trừ thời gian tạm giữ, tạm giam"
        start_date = _parse_date_value(credit.group("from") or "")
        end_date = _parse_date_value(credit.group("to") or "")
        if start_date and end_date:
            credit_text += f" từ {start_date} đến {end_date}"
        fields["detention_credit_text"] = credit_text
    completion_matches = sorted(
        (
            match
            for pattern in _COMPLETION_PATTERNS
            for match in [pattern.search(raw_text)]
            if match is not None
        ),
        key=lambda match: match.start(),
    )
    completion_values = []
    for match in completion_matches:
        folded_match = fold_text(match.group(0))
        value = (
            "đã chấp hành xong hình phạt tù"
            if "chap hanh xong" in folded_match
            else "thời hạn tù bằng thời gian tạm giam"
        )
        if value not in completion_values:
            completion_values.append(value)
    if completion_values:
        fields["completion_text"] = "; ".join(completion_values)
        fields["execution_status"] = "completed"
    if _RELEASE_RE.search(raw_text):
        fields["release_text"] = "được trả tự do tại phiên tòa"

    fields["additional_penalties"] = _additional_penalties(raw_text)
    if fields["is_aggregate"] and fields["primary_penalty_text"]:
        fields["component_penalties"] = [fields["primary_penalty_text"]]
    fields["display_text"] = format_sentence_for_excel(fields)
    return fields


def _blank_sentence_fields() -> dict[str, Any]:
    return {
        "primary_penalty_kind": "unknown",
        "primary_penalty_text": "",
        "display_text": "",
        "duration_years": None,
        "duration_months": None,
        "duration_days": None,
        "suspended": False,
        "probation_duration_years": None,
        "probation_duration_months": None,
        "probation_duration_days": None,
        "probation_text": "",
        "probation_start_text": "",
        "execution_status": "",
        "sentence_start_text": "",
        "detention_credit_text": "",
        "completion_text": "",
        "release_text": "",
        "aggregate_penalty_text": "",
        "component_penalties": [],
        "is_aggregate": False,
        "additional_penalties": [],
    }


def _sentence_record(
    fields: Mapping[str, Any],
    *,
    defendant_entity_ids: list[str],
    defendant_names: list[str],
    source_region: str,
    page_number: int | None,
    line_ids: list[str],
    raw_text: str,
    match_method: str,
    confidence: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        **_blank_sentence_fields(),
        **dict(fields),
        "defendant_entity_ids": defendant_entity_ids,
        "defendant_names": defendant_names,
        "source_region": source_region,
        "page_number": page_number,
        "line_ids": list(dict.fromkeys(line_ids)),
        "raw_text": raw_text,
        "match_method": match_method,
        "confidence": confidence,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _split_distinct_entity_sentences(
    raw_text: str,
    entity_ids: list[str],
    defendants: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if len(entity_ids) < 2 or "moi bi cao" in fold_text(raw_text):
        return {}
    spans: list[tuple[int, str]] = []
    for entity_id in entity_ids:
        name = _defendant_name(entity_id, defendants)
        if not name:
            return {}
        match = re.search(re.escape(name), raw_text, re.I)
        if match is None:
            return {}
        spans.append((match.start(), entity_id))
    spans.sort()
    records: dict[str, dict[str, Any]] = {}
    for index, (start, entity_id) in enumerate(spans):
        end = spans[index + 1][0] if index + 1 < len(spans) else len(raw_text)
        fields = _parse_sentence_fields(raw_text[start:end])
        if not fields["primary_penalty_text"]:
            return {}
        records[entity_id] = fields
    return records


def _trim_sentence_block(block: Mapping[str, Any]) -> dict[str, Any]:
    raw_lines = str(block.get("raw_text") or "").splitlines()
    source_line_ids = [_text(value) for value in block.get("line_ids", [])]
    kept_lines: list[str] = []
    kept_line_ids: list[str] = []
    for index, raw_line in enumerate(raw_lines):
        text = _text(raw_line)
        if _is_sentence_section_boundary(text):
            break
        if not text:
            continue
        kept_lines.append(text)
        if index < len(source_line_ids) and source_line_ids[index]:
            kept_line_ids.append(source_line_ids[index])
    return {
        **dict(block),
        "raw_text": "\n".join(kept_lines),
        "line_ids": kept_line_ids,
        "line_count": len(kept_lines),
    }


def _sentence_lines(
    lines_or_text: str | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(lines_or_text, str):
        return [
            {
                "line_id": f"decision_l{index:04d}",
                "text": value,
                "page_number": None,
            }
            for index, value in enumerate(lines_or_text.splitlines(), start=1)
            if value.strip()
        ]
    return [dict(line) for line in lines_or_text if _text(line.get("text"))]


def _follow_on_clauses(lines: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    clauses: list[list[dict[str, Any]]] = []
    index = 0
    while index < len(lines):
        text = _text(lines[index].get("text"))
        if _is_sentence_section_boundary(text):
            break
        if not _has_follow_on_anchor(text):
            index += 1
            continue
        clause: list[dict[str, Any]] = []
        cursor = index
        while cursor < len(lines) and len(clause) < 4:
            current = _text(lines[cursor].get("text"))
            if _is_sentence_section_boundary(current):
                break
            if cursor > index and _is_numbered_decision_item(current):
                break
            clause.append(lines[cursor])
            if _has_parsed_follow_on(
                _parse_sentence_fields(
                    "\n".join(_text(item.get("text")) for item in clause)
                )
            ):
                cursor += 1
                break
            cursor += 1
        if clause:
            clauses.append(clause)
        index = max(cursor, index + 1)
    return clauses


def _has_follow_on_anchor(value: str) -> bool:
    folded = fold_text(value)
    markers = (
        "phat bo sung",
        "hinh phat chung",
        "thoi gian thu thach",
        "tinh tu ngay tuyen an",
        "thoi han tu tinh tu ngay",
        "tru ngay tam giu",
        "tru thoi gian tam giu",
        "duoc tru thoi gian tam giu",
        "thoi han tu bang",
        "chap hanh xong",
        "tra tu do",
    )
    return any(marker in folded for marker in markers)


def _has_parsed_follow_on(fields: Mapping[str, Any]) -> bool:
    return bool(
        fields.get("aggregate_penalty_text")
        or fields.get("additional_penalties")
        or fields.get("probation_text")
        or fields.get("probation_start_text")
        or fields.get("sentence_start_text")
        or fields.get("detention_credit_text")
        or fields.get("completion_text")
        or fields.get("release_text")
    )


def _is_sentence_section_boundary(value: str) -> bool:
    folded = fold_text(value)
    return any(marker in folded for marker in _SENTENCE_SECTION_BOUNDARIES)


def _is_numbered_decision_item(value: str) -> bool:
    return bool(re.match(r"^\s*\d+(?:\.\d+)*\.?\s+", value))


def _apply_follow_on_details(
    lines_or_text: str | list[dict[str, Any]],
    defendants: list[dict[str, Any]],
    sentence_map: dict[str, dict[str, Any]],
    evidence: list[dict[str, Any]],
    warnings: list[str],
    *,
    min_name_match_score: float,
    name_match_ambiguity_gap: float,
) -> None:
    lines = _sentence_lines(lines_or_text)
    used_line_ids = {
        line_id
        for item in evidence
        for line_id in item.get("line_ids", [])
        if line_id
    }
    for clause_lines in _follow_on_clauses(lines):
        line_ids = [_text(line.get("line_id")) for line in clause_lines]
        line_ids = [line_id for line_id in line_ids if line_id]
        if line_ids and set(line_ids).issubset(used_line_ids):
            continue
        text = "\n".join(_text(line.get("text")) for line in clause_lines)
        fields = _parse_sentence_fields(text)
        clause_warnings = _sentence_completeness_warnings(text, fields)
        if not _evidence_span_is_consistent(text, line_ids):
            clause_warnings.append("sentence_evidence_span_inconsistent")
        warnings.extend(clause_warnings)
        if not _has_parsed_follow_on(fields):
            continue
        matched = match_defendant_entities(
            text,
            defendants,
            min_name_match_score=min_name_match_score,
            name_match_ambiguity_gap=name_match_ambiguity_gap,
        )
        entity_ids = list(matched["defendant_entity_ids"])
        if not entity_ids:
            continue
        entity_names = list(matched["defendant_names"])
        for entity_id in entity_ids:
            existing = sentence_map.get(entity_id)
            if existing is None:
                warnings.append("sentence_execution_details_partial")
                continue
            record = _sentence_record(
                fields,
                defendant_entity_ids=[entity_id],
                defendant_names=[
                    _defendant_name(entity_id, defendants)
                    or next(iter(entity_names), "")
                ],
                source_region=DECISION_TAIL,
                page_number=_optional_int(clause_lines[0].get("page_number")),
                line_ids=line_ids,
                raw_text=text,
                match_method=str(matched["match_method"]),
                confidence="high",
                warnings=clause_warnings,
            )
            _merge_follow_on_sentence(existing, record)
            evidence.append(record)
            used_line_ids.update(line_ids)


def _merge_follow_on_sentence(
    existing: dict[str, Any], record: Mapping[str, Any]
) -> None:
    if record.get("aggregate_penalty_text"):
        existing["aggregate_penalty_text"] = record["aggregate_penalty_text"]
        existing["is_aggregate"] = True
    for key in (
        "probation_text",
        "probation_start_text",
        "sentence_start_text",
        "detention_credit_text",
        "completion_text",
        "release_text",
    ):
        if record.get(key):
            existing[key] = record[key]
    if record.get("execution_status"):
        existing["execution_status"] = record["execution_status"]
    existing["additional_penalties"] = list(
        dict.fromkeys(
            [*existing.get("additional_penalties", []), *record.get("additional_penalties", [])]
        )
    )
    existing["line_ids"] = list(
        dict.fromkeys([*existing.get("line_ids", []), *record.get("line_ids", [])])
    )
    existing["raw_text"] = _join_evidence_text(
        existing.get("raw_text"), record.get("raw_text")
    )
    existing["warnings"] = list(
        dict.fromkeys([*existing.get("warnings", []), *record.get("warnings", [])])
    )


def _join_evidence_text(left: object, right: object) -> str:
    lines: list[str] = []
    for value in (left, right):
        for line in str(value or "").splitlines():
            text = _text(line)
            if text and text not in lines:
                lines.append(text)
    return "\n".join(lines)


def _merge_sentence(
    sentence_map: dict[str, dict[str, Any]],
    entity_id: str,
    record: dict[str, Any],
    warnings: list[str],
) -> None:
    existing = sentence_map.get(entity_id)
    if existing is None:
        sentence_map[entity_id] = record
        return
    if record.get("aggregate_penalty_text"):
        existing["aggregate_penalty_text"] = record["aggregate_penalty_text"]
        existing["is_aggregate"] = True
    elif record.get("primary_penalty_text") != existing.get("primary_penalty_text"):
        warnings.append("multiple_primary_sentences_without_aggregate")
    for key in (
        "probation_text",
        "probation_start_text",
        "sentence_start_text",
        "detention_credit_text",
        "completion_text",
        "release_text",
    ):
        if record.get(key):
            existing[key] = record[key]
    existing["additional_penalties"] = list(
        dict.fromkeys(
            [*existing.get("additional_penalties", []), *record.get("additional_penalties", [])]
        )
    )
    existing["line_ids"] = list(
        dict.fromkeys([*existing.get("line_ids", []), *record.get("line_ids", [])])
    )
    existing["raw_text"] = _join_evidence_text(
        existing.get("raw_text"), record.get("raw_text")
    )
    existing["warnings"] = list(
        dict.fromkeys([*existing.get("warnings", []), *record.get("warnings", [])])
    )


def _additional_penalties(raw_text: str) -> list[str]:
    anchors = list(_ADDITIONAL_ANCHOR_RE.finditer(raw_text))
    if not anchors:
        return []
    penalties: list[str] = []
    money_re = re.compile(
        r"(?:ph(?:ạt|át)\s+bổ\s+sung(?:\s+bị\s+cáo[^\d\n]{0,120})?"
        r"|phạt\s+tiền)\s*(?P<amount>\d[\d. ,]{2,20})\s*đồng",
        re.I,
    )
    for index, anchor in enumerate(anchors):
        end = anchors[index + 1].start() if index + 1 < len(anchors) else len(raw_text)
        segment = raw_text[anchor.start():end]
        for match in money_re.finditer(segment):
            amount = re.sub(r"\s+", "", match.group("amount")).strip(".,")
            if amount:
                penalties.append(f"phạt tiền {amount} đồng")
        if any(money_re.finditer(segment)):
            continue
        inline_segment = raw_text[anchor.end():end]
        inline = inline_segment.splitlines()[0] if inline_segment.splitlines() else ""
        inline = re.sub(r"^[\s:：-]+", "", inline)
        inline = re.split(r"\.(?!\d)", inline, maxsplit=1)[0]
        inline = re.sub(r"\s+", " ", inline).strip(" ,;:.-")
        folded_inline = fold_text(inline)
        known_non_money_penalty = any(
            marker in folded_inline
            for marker in (
                "cam dam nhiem",
                "cam hanh nghe",
                "cam lam cong viec",
                "cam cu tru",
                "quan che",
                "tich thu tai san",
            )
        )
        if (
            inline
            and known_non_money_penalty
            and not any(marker in folded_inline for marker in _CIVIL_MONEY_MARKERS)
        ):
            penalties.append(inline)
    return list(dict.fromkeys(penalties))


def _primary_fine_match(raw_text: str) -> re.Match[str] | None:
    for match in _MONEY_RE.finditer(raw_text):
        context = fold_text(raw_text[max(0, match.start() - 80):match.end()])
        if "phat bo sung" in context:
            continue
        if any(marker in context for marker in _CIVIL_MONEY_MARKERS):
            continue
        return match
    return None


def _set_duration(fields: dict[str, Any], value: str) -> None:
    duration = _duration_values(value)
    fields.update(
        duration_years=duration["years"],
        duration_months=duration["months"],
        duration_days=duration["days"],
    )


def _duration_values(value: str) -> dict[str, int | None]:
    values: dict[str, int | None] = {"years": None, "months": None, "days": None}
    units = {"năm": "years", "tháng": "months", "ngày": "days"}
    for match in _DURATION_COMPONENT_RE.finditer(value):
        values[units[match.group("unit").lower()]] = int(match.group("value"))
    return values


def _format_duration(value: str) -> str:
    parts = []
    for match in _DURATION_COMPONENT_RE.finditer(value):
        parts.append(f"{int(match.group('value'))} {match.group('unit').lower()}")
    return " ".join(parts)


def _duration_before(value: str, end: int) -> str:
    matches = list(re.finditer(_DURATION_SEQUENCE, value[:end], re.I))
    return matches[-1].group(0) if matches else ""


def _normalize_penalty_text(value: str) -> str:
    term = _TERM_RE.search(value)
    if term:
        return f"{_format_duration(term.group('duration'))} tù"
    if re.search(r"tù\s+chung\s+thân", value, re.I):
        return "Tù chung thân"
    if re.search(r"tử\s+hình", value, re.I):
        return "Tử hình"
    return re.sub(r"\s+", " ", value).strip(" ,;:.-")


def _parse_date_value(value: str) -> str | None:
    return parse_vietnamese_date(value) or parse_vietnamese_date(f"ngày {value}")


def _normalize_dates(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return parse_vietnamese_date(match.group(0)) or match.group(0)

    normalized = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", replace, value)
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,;:.-")
    return normalized[0].lower() + normalized[1:] if normalized else ""


def _sentence_completeness_warnings(
    raw_text: str, fields: Mapping[str, Any]
) -> list[str]:
    folded = fold_text(raw_text)
    warnings: list[str] = []
    if (
        "thoi han tu" in folded
        and "tinh tu ngay" in folded
        and not fields.get("sentence_start_text")
    ):
        warnings.append("sentence_start_anchor_unparsed")
    if "thoi gian thu thach" in folded:
        probation_partial = not fields.get("probation_text") or bool(
            re.search(
                r"thời\s+gian\s+thử\s+thách[^\n.;]*,\s*\d{1,3}(?:\s*[.;]|\s*$)",
                raw_text,
                re.I,
            )
        )
        if probation_partial:
            warnings.append("probation_duration_partial")
    if "tinh tu ngay tuyen an" in folded and not fields.get("probation_start_text"):
        warnings.append("probation_start_unparsed")
    credit_anchor = any(
        marker in folded
        for marker in (
            "tru ngay tam giu",
            "tru thoi gian tam giu",
            "duoc tru thoi gian tam giu",
        )
    )
    if credit_anchor and (
        not fields.get("detention_credit_text")
        or (
            "tu ngay" in folded
            and " đến " not in str(fields.get("detention_credit_text") or "")
        )
    ):
        warnings.append("detention_credit_anchor_unparsed")
    completion_anchor = "thoi han tu bang" in folded or "chap hanh xong" in folded
    if completion_anchor and not fields.get("completion_text"):
        warnings.append("completion_anchor_unparsed")
    if "phat bo sung" in folded and not fields.get("additional_penalties"):
        warnings.append("additional_penalty_anchor_unparsed")
    return list(dict.fromkeys(warnings))


def _evidence_span_is_consistent(raw_text: str, line_ids: list[str]) -> bool:
    raw_lines = [line for line in raw_text.splitlines() if line.strip()]
    return bool(raw_lines) and len(raw_lines) == len(line_ids) == len(set(line_ids))


def _decision_only_input(
    lines_or_text: str | Iterable[Mapping[str, Any]],
) -> tuple[str | list[dict[str, Any]], list[str]]:
    if isinstance(lines_or_text, str):
        return lines_or_text, []
    lines = [dict(item) for item in lines_or_text if isinstance(item, Mapping)]
    excluded = {
        _text(item.get("source_region"))
        for item in lines
        if _text(item.get("source_region")) not in {"", DECISION_TAIL}
    }
    allowed = [
        item
        for item in lines
        if _text(item.get("source_region")) in {"", DECISION_TAIL}
    ]
    return allowed, [
        f"sentence_lines_ignored_from_source_region:{region}"
        for region in sorted(excluded)
    ]


def _sentence_mapping_warning(value: str) -> str:
    folded = value.casefold()
    if "ambiguous" in folded:
        return "ambiguous_defendant_sentence_mapping"
    if "unresolved" in folded:
        return "unresolved_collective_defendant_sentence_mapping"
    return "unmatched_defendant_sentence_mapping"


def _defendant_name(entity_id: str, defendants: list[dict[str, Any]]) -> str:
    for item in defendants:
        item_id = _text(item.get("entity_id") or item.get("source_block_id"))
        if item_id == entity_id:
            return _text(item.get("full_name"))
    return ""


def _optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _empty_output(warning: str = "") -> dict[str, Any]:
    return {
        "defendant_sentence_map": {},
        "sentence_evidence": [],
        "warnings": [warning] if warning else [],
        "diagnostics": {
            "sentence_candidate_count": 0,
            "parsed_sentence_count": 0,
            "mapped_defendant_sentence_count": 0,
            "unmapped_sentence_count": 0,
            "invalid_sentence_count": 0,
            "suspended_sentence_count": 0,
            "aggregate_sentence_count": 0,
            "additional_penalty_count": 0,
        },
    }


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ;")
