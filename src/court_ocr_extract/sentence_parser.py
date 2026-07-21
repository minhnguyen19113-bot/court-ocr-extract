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
_DURATION_SEQUENCE = rf"{_DURATION_PART}(?:\s+{_DURATION_PART}){{0,2}}"
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
_ADDITIONAL_RE = re.compile(
    r"(?:hình\s+phạt\s+bổ\s+sung|phạt\s+bổ\s+sung)\s*[:：]?\s*"
    r"(?P<value>[^\n]{2,240}?)(?=\.(?!\d)|\n|$)",
    re.I,
)
_START_RE = re.compile(
    r"thời\s+hạn\s+tù(?:\s+được)?\s+tính\s+từ\s+ngày\s+"
    r"(?P<value>\d{1,2}[/-]\d{1,2}[/-]\d{4}|"
    r"bắt(?:\s+bị\s+cáo)?\s+(?:chấp\s+hành\s+án|giam(?:\s+bị\s+cáo)?\s+để\s+thi\s+hành\s+án))",
    re.I,
)
_DETENTION_CREDIT_RE = re.compile(
    r"(?:được\s+)?trừ\s+thời\s+gian(?:\s+đã)?\s+tạm\s+giữ"
    r"(?:\s*,?\s*tạm\s+giam)?(?:\s+từ\s+ngày\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}"
    r"\s+đến\s+ngày\s+\d{1,2}[/-]\d{1,2}[/-]\d{4})?",
    re.I,
)
_COMPLETION_PATTERNS = (
    re.compile(r"đã\s+chấp\s+hành\s+xong\s+hình\s+phạt\s+tù", re.I),
    re.compile(r"thời\s+hạn\s+tù\s+bằng\s+thời\s+gian\s+tạm\s+giam", re.I),
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

    for block in blocks:
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
            record = _sentence_record(
                fields,
                defendant_entity_ids=[entity_id],
                defendant_names=[name for name in names if name],
                source_region=DECISION_TAIL,
                page_number=_optional_int(block.get("page_number")),
                line_ids=_sentence_line_ids(block, parsed_verdict.line_ids, fields),
                raw_text=raw_text,
                match_method=match_method,
                confidence="high" if entity_id in entity_ids else "medium",
                warnings=[],
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
    if sentence.get("suspended") and primary and "án treo" not in fold_text(primary):
        parts[0] = f"{primary}, cho hưởng án treo"
    if probation:
        parts.append(probation)
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

    start = _START_RE.search(raw_text)
    if start:
        value = start.group("value")
        parsed_date = parse_vietnamese_date(value)
        normalized = parsed_date or re.sub(r"\s+", " ", value).strip()
        normalized = re.sub(r"^bắt\s+bị\s+cáo\s+", "bắt ", normalized, flags=re.I)
        fields["sentence_start_text"] = f"thời hạn tù tính từ ngày {normalized}"

    credit = _DETENTION_CREDIT_RE.search(raw_text)
    if credit:
        fields["detention_credit_text"] = _normalize_dates(
            re.sub(r"^trừ\s+", "được trừ ", credit.group(0), flags=re.I)
        )
    completion_matches = sorted(
        (
            match
            for pattern in _COMPLETION_PATTERNS
            for match in [pattern.search(raw_text)]
            if match is not None
        ),
        key=lambda match: match.start(),
    )
    completion_values = [
        re.sub(r"\s+", " ", match.group(0)).strip().lower()
        for match in completion_matches
    ]
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
    if isinstance(lines_or_text, str):
        lines = [
            {"line_id": f"decision_l{index:04d}", "text": value, "page_number": None}
            for index, value in enumerate(lines_or_text.splitlines(), start=1)
            if value.strip()
        ]
    else:
        lines = lines_or_text
    for line in lines:
        text = _text(line.get("text"))
        fields = _parse_sentence_fields(text)
        has_follow_on = bool(
            fields["aggregate_penalty_text"]
            or fields["additional_penalties"]
            or fields["release_text"]
        )
        if not has_follow_on:
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
        for entity_id in entity_ids:
            existing = sentence_map.get(entity_id)
            if existing is None:
                warnings.append("sentence_execution_details_partial")
                continue
            if fields["aggregate_penalty_text"]:
                existing["aggregate_penalty_text"] = fields["aggregate_penalty_text"]
                existing["is_aggregate"] = True
            existing["additional_penalties"] = list(
                dict.fromkeys(
                    [*existing.get("additional_penalties", []), *fields["additional_penalties"]]
                )
            )
            if fields["release_text"]:
                existing["release_text"] = fields["release_text"]
            existing["line_ids"] = list(
                dict.fromkeys([*existing.get("line_ids", []), _text(line.get("line_id"))])
            )


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


def _sentence_line_ids(
    block: Mapping[str, Any],
    verdict_line_ids: list[str],
    fields: Mapping[str, Any],
) -> list[str]:
    line_ids = list(verdict_line_ids)
    raw_lines = str(block.get("raw_text") or "").splitlines()
    block_line_ids = [str(value) for value in block.get("line_ids", [])]
    markers = (
        "thoi gian thu thach",
        "thoi han tu",
        "tru thoi gian",
        "chap hanh xong",
        "tra tu do",
        "hinh phat bo sung",
        "hinh phat chung",
    )
    for index, raw_line in enumerate(raw_lines):
        if any(marker in fold_text(raw_line) for marker in markers) and index < len(block_line_ids):
            line_ids.append(block_line_ids[index])
    return list(dict.fromkeys(value for value in line_ids if value))


def _additional_penalties(raw_text: str) -> list[str]:
    penalties: list[str] = []
    for match in _ADDITIONAL_RE.finditer(raw_text):
        value = re.split(
            r"\s+(?:án\s+phí|bồi\s+thường|truy\s+thu|tịch\s+thu|tiêu\s+hủy)\b",
            match.group("value"),
            maxsplit=1,
            flags=re.I,
        )[0]
        value = re.sub(r"\s+", " ", value).strip(" ,;:.-")
        if value:
            penalties.append(value)
    return list(dict.fromkeys(penalties))


def _primary_fine_match(raw_text: str) -> re.Match[str] | None:
    for match in _MONEY_RE.finditer(raw_text):
        context = fold_text(raw_text[max(0, match.start() - 80):match.end()])
        if "hinh phat bo sung" in context:
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


def _normalize_dates(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return parse_vietnamese_date(match.group(0)) or match.group(0)

    normalized = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", replace, value)
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,;:.-")
    return normalized[0].lower() + normalized[1:] if normalized else ""


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
