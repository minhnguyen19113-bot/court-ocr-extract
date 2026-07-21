from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from difflib import SequenceMatcher
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
    r"(?:thời\s+hạn\s+tù|thời\s+hạn\s+chấp\s+hành\s+hình\s+phạt\s+tù)"
    r"(?:\s+được)?\s+(?:tính|tỉnh)(?:\s+kể)?\s+(?:từ|tử)\s+ngày\s+"
    rf"(?P<value>{_DATE_VALUE}|"
    r"bắt(?:\s+bị\s+cáo)?\s+chấp\s+hành\s+án|"
    r"(?:bắt\s+giam|bất\s+giam|bắt\s+giảm)\s+bị\s+cáo\s+để\s+thi\s+hành\s+án)",
    re.I,
)
_START_ANCHOR_RE = re.compile(
    r"(?:thời\s+hạn\s+tù|thời\s+hạn\s+chấp\s+hành\s+hình\s+phạt\s+tù)"
    r"(?:\s+được)?\s+(?:tính|tỉnh)(?:\s+kể)?\s+(?:từ|tử)\s+ngày\b",
    re.I,
)
_PROBATION_START_RE = re.compile(
    rf"(?P<value>tính\s+từ\s+ngày\s+tuyên\s+án"
    rf"(?:\s+sơ\s+th(?:ẩm|ảm|ẳm))?"
    rf"(?:\s*(?:\(\s*|ngày\s+)?(?P<date>{_DATE_VALUE})\s*\)?)?)",
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
    "khang cao",
    "noi nhan",
)
_SENTENCE_PROCEDURAL_BOUNDARIES = (
    "tiep tuc tam giam",
    "tam giam bi cao trong thoi han",
    "giao bi cao cho uy ban nhan dan",
    "giao cho uy ban nhan dan",
    "giao nguoi duoc huong an treo",
    "trong thoi gian thu thach",
    "nguoi duoc huong an treo co y vi pham",
    "neu co y vi pham nghia vu",
    "thay doi noi cu tru",
    "gia dinh bi cao co trach nhiem",
)
_ADMINISTRATIVE_TAIL_MARKERS = (
    "xac nhan hien trang ho so",
    "van phong nhan",
    "nguoi giao",
    "nguoi nhan",
    "bien ban giao nhan",
    "danh sach nguoi bi ket an",
    "stt bi cao muc an",
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
SENTENCE_REVIEW_WARNINGS = {
    *SENTENCE_COMPLETENESS_WARNINGS,
    "cross_source_person_name_disagreement",
    "ambiguous_defendant_sentence_mapping",
}


def parse_defendant_sentences(
    lines_or_text: str | Iterable[Mapping[str, Any]],
    *,
    defendants: Iterable[Mapping[str, Any]] = (),
    source_region: str = DECISION_TAIL,
    case_id: str = "",
    min_name_match_score: float = 88.0,
    name_match_ambiguity_gap: float = 5.0,
) -> dict[str, Any]:
    if source_region != DECISION_TAIL:
        return _empty_output(f"sentence_source_region_not_allowed:{source_region}")

    defendant_list = [dict(item) for item in defendants if isinstance(item, Mapping)]
    decision_input, source_warnings = _decision_only_input(lines_or_text)
    decision_input = _authoritative_sentence_input(decision_input)
    decision_lines = _sentence_lines(decision_input)
    blocks = iter_verdict_blocks(decision_input)
    sentence_map: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    warning_records: list[dict[str, Any]] = []
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
        raw_source_text = _span_raw_text(
            _source_lines_for_ids(decision_lines, block.get("line_ids", []))
        ) or raw_text
        entity_ids = list(parsed_verdict.defendant_entity_ids)
        entity_names = list(parsed_verdict.defendant_names)
        match_method = parsed_verdict.match_method
        match_warning = parsed_verdict.warning if not entity_ids else ""
        if not entity_ids and "ambiguous" not in match_warning.casefold():
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
            mapping_warning = _sentence_mapping_warning(match_warning)
            warnings.append(mapping_warning)
            if mapping_warning == "ambiguous_defendant_sentence_mapping":
                decision_name = _decision_sentence_name(raw_source_text)
                warning_records.append(
                    _sentence_warning_record(
                        case_id=case_id,
                        warning=mapping_warning,
                        scope="case",
                        defendant_entity_id="",
                        defendant_name="",
                        page_number=_optional_int(block.get("page_number")),
                        line_ids=list(block.get("line_ids", [])),
                        raw_text=raw_text,
                        decision_name=decision_name,
                        decision_raw_name=decision_name,
                        normalized_decision_name=fold_text(
                            _strip_name_honorific(decision_name)
                        ),
                        match_method="ambiguous",
                    )
                )

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
            front_name = _defendant_name(entity_id, defendant_list)
            primary_lines = _source_lines_for_ids(
                decision_lines, parsed_verdict.line_ids
            )
            if not primary_lines:
                primary_lines = _block_lines_for_ids(block, parsed_verdict.line_ids)
            if not primary_lines:
                primary_lines = _block_lines_for_ids(
                    block, list(block.get("line_ids", []))[:1]
                )
            primary_clause = _evidence_clause_payload(
                primary_lines, "primary_penalty"
            )
            primary_raw_text = primary_clause["raw_text"]
            line_ids = primary_clause["line_ids"]
            primary_fields = _fields_for_evidence_type(
                "primary_penalty", fields
            )
            name_audit = _cross_source_name_audit(
                primary_raw_text,
                front_name=front_name,
                match_method=match_method,
            )
            record_warnings: list[str] = []
            if name_audit["name_disagreement"]:
                record_warnings.append("cross_source_person_name_disagreement")
                warnings.append("cross_source_person_name_disagreement")
                warning_records.append(
                    _sentence_warning_record(
                        case_id=case_id,
                        warning="cross_source_person_name_disagreement",
                        scope="entity",
                        defendant_entity_id=entity_id,
                        defendant_name=front_name,
                        page_number=_optional_int(block.get("page_number")),
                        line_ids=line_ids,
                        raw_text=primary_raw_text,
                        **name_audit,
                    )
                )
            if not _evidence_span_is_consistent(
                primary_raw_text, line_ids, primary_clause["clause_spans"]
            ):
                record_warnings.append("sentence_evidence_span_inconsistent")
                warnings.append("sentence_evidence_span_inconsistent")
                warning_records.append(
                    _sentence_warning_record(
                        case_id=case_id,
                        warning="sentence_evidence_span_inconsistent",
                        scope="entity",
                        defendant_entity_id=entity_id,
                        defendant_name=front_name,
                        page_number=_optional_int(block.get("page_number")),
                        line_ids=line_ids,
                        raw_text=primary_raw_text,
                    )
                )
            record = _sentence_record(
                primary_fields,
                evidence_type="primary_penalty",
                defendant_entity_ids=[entity_id],
                defendant_names=[front_name] if front_name else [],
                source_region=DECISION_TAIL,
                page_number=_optional_int(block.get("page_number")),
                line_ids=line_ids,
                raw_text=primary_raw_text,
                raw_clause=primary_clause["raw_clause"],
                clause_spans=primary_clause["clause_spans"],
                match_method=name_audit["name_match_method"],
                confidence="high" if entity_id in entity_ids else "medium",
                warnings=record_warnings,
                audit=name_audit,
            )
            _merge_sentence(sentence_map, entity_id, deepcopy(record), warnings)
            evidence.append(record)
            parsed_count += 1

    _apply_follow_on_details(
        decision_input,
        defendant_list,
        sentence_map,
        evidence,
        warnings,
        warning_records,
        case_id=case_id,
        min_name_match_score=min_name_match_score,
        name_match_ambiguity_gap=name_match_ambiguity_gap,
    )

    _validate_sentence_aggregates(
        sentence_map,
        evidence,
        warnings,
        warning_records,
        defendants=defendant_list,
        case_id=case_id,
    )

    for record in sentence_map.values():
        record["display_text"] = format_sentence_for_excel(record)

    mapped_count = len(sentence_map)
    if mapped_count < len(defendant_list):
        warnings.append(f"sentence_coverage_incomplete:{mapped_count}/{len(defendant_list)}")
    warning_records = _complete_sentence_warning_records(
        case_id=case_id,
        warnings=warnings,
        warning_records=warning_records,
        evidence=evidence,
        lines=_sentence_lines(decision_input),
    )
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
        "sentence_warnings": warning_records,
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
    evidence_type: str,
    defendant_entity_ids: list[str],
    defendant_names: list[str],
    source_region: str,
    page_number: int | None,
    line_ids: list[str],
    raw_text: str,
    raw_clause: str,
    clause_spans: list[dict[str, Any]],
    match_method: str,
    confidence: str,
    warnings: list[str],
    audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    audit_fields = dict(audit or {})
    front_name = _text(audit_fields.get("front_name"))
    decision_name = str(audit_fields.get("decision_name") or "").strip()
    return {
        **_blank_sentence_fields(),
        **dict(fields),
        "evidence_type": evidence_type,
        "defendant_entity_ids": defendant_entity_ids,
        "defendant_names": defendant_names,
        "source_region": source_region,
        "page_number": page_number,
        "line_ids": list(dict.fromkeys(line_ids)),
        "raw_text": raw_text,
        "raw_clause": raw_clause,
        "clause_spans": clause_spans,
        "match_method": match_method,
        "confidence": confidence,
        "warnings": list(dict.fromkeys(warnings)),
        "front_names": [front_name] if front_name else list(defendant_names),
        "decision_names": [decision_name] if decision_name else [],
        "front_entity_name": front_name,
        "decision_raw_name": decision_name,
        "normalized_front_name": "",
        "normalized_decision_name": "",
        "similarity": None,
        **audit_fields,
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


def _typed_detail_clauses(
    lines: list[dict[str, Any]],
) -> list[tuple[str, list[dict[str, Any]]]]:
    clauses: list[tuple[str, list[dict[str, Any]]]] = []
    evidence_types = (
        "probation",
        "sentence_start",
        "detention_credit",
        "completion",
        "release",
        "aggregate_penalty",
        "additional_penalty",
    )
    for evidence_type in evidence_types:
        used_line_ids: set[str] = set()
        for index, line in enumerate(lines):
            line_id = _text(line.get("line_id"))
            text = _text(line.get("text"))
            if line_id in used_line_ids or _is_sentence_evidence_boundary(text):
                continue
            if not _has_evidence_anchor(evidence_type, text):
                continue
            clause = _collect_typed_clause(lines, index, evidence_type)
            if not clause:
                continue
            clauses.append((evidence_type, clause))
            used_line_ids.update(_span_line_ids(clause))
    clauses.sort(
        key=lambda item: min(
            (
                index
                for index, line in enumerate(lines)
                if _text(line.get("line_id")) in set(_span_line_ids(item[1]))
            ),
            default=len(lines),
        )
    )
    return clauses


def _collect_typed_clause(
    lines: list[dict[str, Any]], start: int, evidence_type: str
) -> list[dict[str, Any]]:
    clause: list[dict[str, Any]] = []
    cursor = start
    while cursor < len(lines) and len(clause) < 4:
        current = _text(lines[cursor].get("text"))
        if cursor > start and (
            _is_sentence_evidence_boundary(current)
            or _is_numbered_decision_item(current)
        ):
            break
        clause.append(lines[cursor])
        fields = _parse_sentence_fields(_span_raw_text(clause))
        next_line = lines[cursor + 1] if cursor + 1 < len(lines) else None
        if _typed_clause_is_complete(evidence_type, fields, clause):
            if not _typed_clause_needs_next(evidence_type, fields, clause, next_line):
                break
        cursor += 1
    return clause


def _has_evidence_anchor(evidence_type: str, value: str) -> bool:
    folded = fold_text(value)
    markers = {
        "probation": ("cho huong an treo", "thoi gian thu thach", "tinh tu ngay tuyen an"),
        "sentence_start": (
            "thoi han tu tinh tu ngay",
            "thoi han tu duoc tinh tu ngay",
            "thoi han tu duoc tinh ke tu ngay",
            "thoi han tu duoc tinh tu ngay",
            "thoi han tu duoc tinh tu ngay",
            "thoi han chap hanh hinh phat tu tinh tu ngay",
        ),
        "detention_credit": (
            "tru ngay tam giu",
            "tru thoi gian tam giu",
            "duoc tru thoi gian tam giu",
        ),
        "completion": ("thoi han tu bang", "chap hanh xong"),
        "release": ("tra tu do",),
        "aggregate_penalty": ("hinh phat chung",),
        "additional_penalty": ("phat bo sung",),
    }
    return any(marker in folded for marker in markers[evidence_type])


def _typed_clause_is_complete(
    evidence_type: str,
    fields: Mapping[str, Any],
    clause: list[dict[str, Any]],
) -> bool:
    if evidence_type == "probation":
        folded = fold_text(_span_raw_text(clause))
        return bool(fields.get("probation_text")) and (
            "tinh tu ngay tuyen an" not in folded
            or bool(fields.get("probation_start_text"))
        )
    return bool(
        {
            "sentence_start": fields.get("sentence_start_text"),
            "detention_credit": fields.get("detention_credit_text"),
            "completion": fields.get("completion_text"),
            "release": fields.get("release_text"),
            "aggregate_penalty": fields.get("aggregate_penalty_text"),
            "additional_penalty": fields.get("additional_penalties"),
        }[evidence_type]
    )


def _typed_clause_needs_next(
    evidence_type: str,
    fields: Mapping[str, Any],
    clause: list[dict[str, Any]],
    next_line: dict[str, Any] | None,
) -> bool:
    if next_line is None:
        return False
    next_text = _text(next_line.get("text"))
    if _is_sentence_evidence_boundary(next_text) or _is_numbered_decision_item(next_text):
        return False
    if evidence_type == "probation":
        if _has_evidence_anchor("probation", next_text):
            return True
        return bool(fields.get("probation_start_text")) and _looks_like_date_line(next_text)
    if evidence_type == "completion":
        return _has_evidence_anchor("completion", next_text)
    if evidence_type == "detention_credit":
        raw_text = _span_raw_text(clause)
        folded = fold_text(raw_text)
        return (
            "tu ngay" in folded
            and "den ngay" not in folded
            and bool(re.search(_DATE_VALUE, raw_text, re.I))
        )
    return False


def _is_sentence_section_boundary(value: str) -> bool:
    folded = fold_text(value)
    return any(marker in folded for marker in _SENTENCE_SECTION_BOUNDARIES)


def _is_sentence_evidence_boundary(value: str) -> bool:
    folded = fold_text(value)
    return _is_sentence_section_boundary(value) or any(
        marker in folded for marker in _SENTENCE_PROCEDURAL_BOUNDARIES
    )


def _is_numbered_decision_item(value: str) -> bool:
    return bool(re.match(r"^\s*\d+(?:\.\d+)*\.?\s+", value))


def _looks_like_date_line(value: str) -> bool:
    return bool(re.fullmatch(rf"\s*\(?\s*(?:ngày\s+)?{_DATE_VALUE}\s*\)?[.;]?\s*", value, re.I))


def _span_line_ids(lines: Iterable[Mapping[str, Any]]) -> list[str]:
    return list(
        dict.fromkeys(
            _text(line.get("line_id"))
            for line in lines
            if _text(line.get("line_id"))
        )
    )


def _span_raw_text(lines: Iterable[Mapping[str, Any]]) -> str:
    return "\n".join(
        _text(line.get("text"))
        for line in lines
        if _text(line.get("text"))
    )


def _evidence_clause_payload(
    lines: list[dict[str, Any]], evidence_type: str
) -> dict[str, Any]:
    raw_lines = [str(line.get("text") or "") for line in lines]
    joined = "\n".join(raw_lines)
    start, end = _evidence_clause_bounds(joined, evidence_type)
    while start < end and joined[start].isspace():
        start += 1
    while end > start and joined[end - 1].isspace():
        end -= 1

    spans: list[dict[str, Any]] = []
    cursor = 0
    for line, raw_line in zip(lines, raw_lines, strict=True):
        line_start = cursor
        line_end = line_start + len(raw_line)
        overlap_start = max(start, line_start)
        overlap_end = min(end, line_end)
        if overlap_start < overlap_end:
            char_start = overlap_start - line_start
            char_end = overlap_end - line_start
            raw_clause = raw_line[char_start:char_end]
            if raw_clause.strip():
                spans.append(
                    {
                        "line_id": _text(line.get("line_id")),
                        "raw_line_text": raw_line,
                        "raw_clause": raw_clause,
                        "char_start": char_start,
                        "char_end": char_end,
                    }
                )
        cursor = line_end + 1

    raw_clause = "\n".join(span["raw_clause"] for span in spans)
    return {
        "raw_text": raw_clause,
        "raw_clause": raw_clause,
        "line_ids": list(
            dict.fromkeys(span["line_id"] for span in spans if span["line_id"])
        ),
        "clause_spans": spans,
    }


def _evidence_clause_bounds(raw_text: str, evidence_type: str) -> tuple[int, int]:
    if not raw_text:
        return 0, 0
    matches: list[re.Match[str]] = []
    if evidence_type == "sentence_start":
        matches = [match for match in (_START_RE.search(raw_text),) if match]
        if not matches:
            anchor = _START_ANCHOR_RE.search(raw_text)
            if anchor:
                return _expand_clause_bounds(raw_text, anchor.start(), anchor.end())
    elif evidence_type == "detention_credit":
        matches = [match for match in (_DETENTION_CREDIT_RE.search(raw_text),) if match]
    elif evidence_type == "completion":
        matches = [
            match
            for pattern in _COMPLETION_PATTERNS
            for match in [pattern.search(raw_text)]
            if match
        ]
    elif evidence_type == "release":
        matches = [match for match in (_RELEASE_RE.search(raw_text),) if match]
    elif evidence_type == "aggregate_penalty":
        matches = [match for match in (_AGGREGATE_RE.search(raw_text),) if match]
    elif evidence_type == "additional_penalty":
        anchor = _ADDITIONAL_ANCHOR_RE.search(raw_text)
        if anchor:
            return _expand_clause_bounds(raw_text, anchor.start(), anchor.end())
    elif evidence_type == "probation":
        matches = [
            match
            for match in (
                _SUSPENDED_RE.search(raw_text),
                _PROBATION_RE.search(raw_text),
                _PROBATION_START_RE.search(raw_text),
            )
            if match
        ]
    elif evidence_type == "primary_penalty":
        starts = [
            match.start()
            for match in (
                _PROBATION_RE.search(raw_text),
                _SUSPENDED_RE.search(raw_text),
                _START_ANCHOR_RE.search(raw_text),
                _DETENTION_CREDIT_RE.search(raw_text),
                *[pattern.search(raw_text) for pattern in _COMPLETION_PATTERNS],
                _RELEASE_RE.search(raw_text),
                _AGGREGATE_RE.search(raw_text),
                _ADDITIONAL_ANCHOR_RE.search(raw_text),
            )
            if match is not None
        ]
        return 0, min(starts, default=len(raw_text))

    if not matches:
        return 0, len(raw_text)
    return _expand_clause_bounds(
        raw_text,
        min(match.start() for match in matches),
        max(match.end() for match in matches),
    )


def _expand_clause_bounds(raw_text: str, start: int, parsed_end: int) -> tuple[int, int]:
    following = raw_text[parsed_end:]
    boundary = re.search(r"[.;](?=\s|$)|\n\s*\d+(?:\.\d+)*\.?\s+", following)
    end = parsed_end + (boundary.start() + 1 if boundary else len(following))
    return start, end


def _block_lines_for_ids(
    block: Mapping[str, Any], line_ids: Iterable[object]
) -> list[dict[str, Any]]:
    wanted = {_text(value) for value in line_ids if _text(value)}
    raw_lines = str(block.get("raw_text") or "").splitlines()
    block_line_ids = [_text(value) for value in block.get("line_ids", [])]
    return [
        {
            "line_id": line_id,
            "page_number": block.get("page_number"),
            "text": raw_lines[index],
        }
        for index, line_id in enumerate(block_line_ids)
        if line_id in wanted and index < len(raw_lines)
    ]


def _source_lines_for_ids(
    lines: list[dict[str, Any]], line_ids: Iterable[object]
) -> list[dict[str, Any]]:
    wanted = {_text(value) for value in line_ids if _text(value)}
    return [line for line in lines if _text(line.get("line_id")) in wanted]


def _nearest_primary_entity_ids(
    clause_lines: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    line_indexes: Mapping[str, int],
) -> list[str]:
    clause_indexes = [
        line_indexes[line_id]
        for line_id in _span_line_ids(clause_lines)
        if line_id in line_indexes
    ]
    if not clause_indexes:
        return []
    clause_start = min(clause_indexes)
    candidates: list[tuple[int, list[str]]] = []
    for item in evidence:
        if item.get("evidence_type") != "primary_penalty":
            continue
        indexes = [
            line_indexes[line_id]
            for line_id in item.get("line_ids", [])
            if line_id in line_indexes
        ]
        if indexes and max(indexes) <= clause_start:
            candidates.append((max(indexes), list(item.get("defendant_entity_ids", []))))
    return max(candidates, default=(-1, []), key=lambda item: item[0])[1]


def _has_parsed_evidence(
    evidence_type: str, fields: Mapping[str, Any]
) -> bool:
    return bool(
        {
            "probation": fields.get("suspended") or fields.get("probation_text"),
            "sentence_start": fields.get("sentence_start_text"),
            "detention_credit": fields.get("detention_credit_text"),
            "completion": fields.get("completion_text"),
            "release": fields.get("release_text"),
            "aggregate_penalty": fields.get("aggregate_penalty_text"),
            "additional_penalty": fields.get("additional_penalties"),
        }[evidence_type]
    )


def _fields_for_evidence_type(
    evidence_type: str, fields: Mapping[str, Any]
) -> dict[str, Any]:
    keys = {
        "primary_penalty": (
            "primary_penalty_kind",
            "primary_penalty_text",
            "duration_years",
            "duration_months",
            "duration_days",
        ),
        "probation": (
            "suspended",
            "probation_duration_years",
            "probation_duration_months",
            "probation_duration_days",
            "probation_text",
            "probation_start_text",
        ),
        "sentence_start": ("sentence_start_text",),
        "detention_credit": ("detention_credit_text",),
        "completion": ("completion_text", "execution_status"),
        "release": ("release_text",),
        "aggregate_penalty": (
            "aggregate_penalty_text",
            "component_penalties",
            "is_aggregate",
        ),
        "additional_penalty": ("additional_penalties",),
    }[evidence_type]
    selected = _blank_sentence_fields()
    for key in keys:
        selected[key] = fields.get(key)
    if evidence_type == "primary_penalty" and fields.get("suspended"):
        selected["primary_penalty_kind"] = "term_imprisonment"
    if evidence_type == "probation" and fields.get("suspended"):
        selected["primary_penalty_kind"] = "suspended_imprisonment"
        selected["execution_status"] = "suspended"
    selected["display_text"] = format_sentence_for_excel(selected)
    return selected


def _apply_follow_on_details(
    lines_or_text: str | list[dict[str, Any]],
    defendants: list[dict[str, Any]],
    sentence_map: dict[str, dict[str, Any]],
    evidence: list[dict[str, Any]],
    warnings: list[str],
    warning_records: list[dict[str, Any]],
    *,
    case_id: str,
    min_name_match_score: float,
    name_match_ambiguity_gap: float,
) -> None:
    lines = _sentence_lines(lines_or_text)
    line_indexes = {
        _text(line.get("line_id")): index
        for index, line in enumerate(lines)
        if _text(line.get("line_id"))
    }
    for evidence_type, clause_lines in _typed_detail_clauses(lines):
        full_text = _span_raw_text(clause_lines)
        clause = _evidence_clause_payload(clause_lines, evidence_type)
        line_ids = clause["line_ids"]
        text = clause["raw_text"]
        parsed_fields = _parse_sentence_fields(full_text)
        fields = _fields_for_evidence_type(evidence_type, parsed_fields)
        clause_warnings: list[str] = []
        if not _evidence_span_is_consistent(
            text, line_ids, clause["clause_spans"]
        ):
            clause_warnings.append("sentence_evidence_span_inconsistent")
        warnings.extend(clause_warnings)
        matched = match_defendant_entities(
            full_text,
            defendants,
            min_name_match_score=min_name_match_score,
            name_match_ambiguity_gap=name_match_ambiguity_gap,
        )
        entity_ids = list(matched["defendant_entity_ids"])
        match_method = str(matched["match_method"])
        if not entity_ids:
            entity_ids = _nearest_primary_entity_ids(
                clause_lines, evidence, line_indexes
            )
            if entity_ids:
                match_method = "preceding_primary_sentence"
        entity_names = list(matched["defendant_names"])
        if clause_warnings:
            targets = entity_ids or [""]
            for entity_id in targets:
                warning_records.extend(
                    _sentence_warning_record(
                        case_id=case_id,
                        warning=warning,
                        scope="entity" if entity_id else "case",
                        defendant_entity_id=entity_id,
                        defendant_name=_defendant_name(entity_id, defendants),
                        page_number=_optional_int(clause_lines[0].get("page_number")),
                        line_ids=line_ids,
                        raw_text=text,
                    )
                    for warning in clause_warnings
                )
        if not entity_ids:
            evidence.append(
                _sentence_record(
                    fields,
                    evidence_type=evidence_type,
                    defendant_entity_ids=[],
                    defendant_names=entity_names,
                    source_region=DECISION_TAIL,
                    page_number=_optional_int(clause_lines[0].get("page_number")),
                    line_ids=line_ids,
                    raw_text=text,
                    raw_clause=clause["raw_clause"],
                    clause_spans=clause["clause_spans"],
                    match_method=match_method,
                    confidence="low",
                    warnings=clause_warnings,
                )
            )
            continue
        for entity_id in entity_ids:
            existing = sentence_map.get(entity_id)
            if existing is None:
                warnings.append("sentence_execution_details_partial")
                continue
            record = _sentence_record(
                fields,
                evidence_type=evidence_type,
                defendant_entity_ids=[entity_id],
                defendant_names=[
                    _defendant_name(entity_id, defendants)
                    or next(iter(entity_names), "")
                ],
                source_region=DECISION_TAIL,
                page_number=_optional_int(clause_lines[0].get("page_number")),
                line_ids=line_ids,
                raw_text=text,
                raw_clause=clause["raw_clause"],
                clause_spans=clause["clause_spans"],
                match_method=match_method,
                confidence="high",
                warnings=clause_warnings,
            )
            if _has_parsed_evidence(evidence_type, fields):
                _merge_follow_on_sentence(existing, record)
            evidence.append(record)


def _merge_follow_on_sentence(
    existing: dict[str, Any], record: Mapping[str, Any]
) -> None:
    if record.get("suspended"):
        existing["suspended"] = True
        existing["primary_penalty_kind"] = "suspended_imprisonment"
        existing["execution_status"] = "suspended"
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
    for key in (
        "probation_duration_years",
        "probation_duration_months",
        "probation_duration_days",
    ):
        if record.get(key) is not None:
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
    if _has_evidence_anchor("sentence_start", raw_text) and not fields.get(
        "sentence_start_text"
    ):
        warnings.append("sentence_start_anchor_unparsed")
    if "thoi gian thu thach" in folded:
        if _probation_duration_is_partial(raw_text):
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


def _cross_source_name_audit(
    raw_text: str, *, front_name: str, match_method: str
) -> dict[str, Any]:
    decision_name = _decision_sentence_name(raw_text)
    normalized_front = fold_text(_strip_name_honorific(front_name))
    normalized_decision = fold_text(_strip_name_honorific(decision_name))
    similarity = (
        round(
            SequenceMatcher(None, normalized_front, normalized_decision).ratio() * 100,
            2,
        )
        if normalized_front and normalized_decision
        else None
    )
    matcher_method = match_method.casefold()
    if "ambiguous" in matcher_method:
        semantic_method = "ambiguous"
    elif "fuzzy" in matcher_method:
        semantic_method = "unique_fuzzy"
    elif not decision_name:
        semantic_method = "unmatched"
    elif front_name.strip() == decision_name.strip():
        semantic_method = "exact"
    elif normalized_front and normalized_front == normalized_decision:
        semantic_method = "normalization_only"
    else:
        semantic_method = "unmatched"
    return {
        "front_name": front_name,
        "decision_name": decision_name,
        "front_entity_name": front_name,
        "decision_raw_name": decision_name,
        "normalized_front_name": normalized_front,
        "normalized_decision_name": normalized_decision,
        "name_match_method": semantic_method,
        "matcher_match_method": match_method,
        "similarity": similarity,
        "name_disagreement": bool(
            semantic_method == "unique_fuzzy"
            and normalized_front
            and normalized_decision
            and normalized_front != normalized_decision
        ),
    }


def _decision_sentence_name(raw_text: str) -> str:
    match = re.search(
        rf"(?:xử\s+phạt|tuyên\s+phạt|tuyên\s+xử)\s+"
        rf"(?:bị\s+cáo\s+)?(?P<name>[^\n,;:]{{2,160}}?)"
        rf"(?=\s+(?:{_DURATION_PART}|tù\s+chung\s+thân|tử\s+hình|"
        rf"cải\s+tạo\s+không\s+giam\s+giữ|phạt\s+tiền|về\s+tội|phạm\s+tội)\b)",
        raw_text,
        re.I,
    )
    return str(match.group("name") or "").strip(" ,;:") if match else ""


def _strip_name_honorific(value: str) -> str:
    return re.sub(
        r"^(?:bị\s+cáo|ông|bà|anh|chị)\s+",
        "",
        _text(value),
        flags=re.I,
    )


def _sentence_warning_record(
    *,
    case_id: str,
    warning: str,
    scope: str,
    defendant_entity_id: str,
    defendant_name: str,
    page_number: int | None,
    line_ids: list[str],
    raw_text: str,
    severity: str = "warning",
    **audit: Any,
) -> dict[str, Any]:
    record = {
        "case_id": case_id,
        "warning": warning,
        "severity": severity,
        "scope": scope,
        "defendant_entity_id": defendant_entity_id,
        "defendant_name": defendant_name,
        "page_number": page_number,
        "line_ids": list(dict.fromkeys(line_ids)),
        "raw_text": raw_text,
        "source_region": DECISION_TAIL,
        "front_name": "",
        "decision_name": "",
        "front_entity_name": "",
        "decision_raw_name": "",
        "normalized_front_name": "",
        "normalized_decision_name": "",
        "match_method": "",
        "similarity": None,
    }
    record.update(audit)
    if audit.get("name_match_method") and not audit.get("match_method"):
        record["match_method"] = audit["name_match_method"]
    return record


def _complete_sentence_warning_records(
    *,
    case_id: str,
    warnings: list[str],
    warning_records: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    lines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records = list(warning_records)
    existing_codes = {str(record.get("warning") or "") for record in records}
    first_source = evidence[0] if evidence else (lines[0] if lines else {})
    for warning in dict.fromkeys(value for value in warnings if value):
        if warning in existing_codes:
            continue
        records.append(
            _sentence_warning_record(
                case_id=case_id,
                warning=warning,
                severity=("info" if "ignored_from_source_region" in warning else "warning"),
                scope="case",
                defendant_entity_id="",
                defendant_name="",
                page_number=_optional_int(first_source.get("page_number")),
                line_ids=[
                    _text(value)
                    for value in first_source.get("line_ids", [])
                    if _text(value)
                ]
                or ([
                    _text(first_source.get("line_id"))
                ] if _text(first_source.get("line_id")) else []),
                raw_text=str(
                    first_source.get("raw_text") or first_source.get("text") or ""
                ).strip(),
            )
        )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, int | None, tuple[str, ...]]] = set()
    for record in records:
        key = (
            str(record.get("case_id") or ""),
            str(record.get("warning") or ""),
            str(record.get("scope") or ""),
            str(record.get("defendant_entity_id") or ""),
            _optional_int(record.get("page_number")),
            tuple(record.get("line_ids", [])),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(record)
    return deduped


def _probation_duration_is_partial(raw_text: str) -> bool:
    match = _PROBATION_RE.search(raw_text)
    if match is None or not _DURATION_COMPONENT_RE.search(match.group("duration")):
        return True
    remainder = raw_text[match.end():]
    remainder = re.split(
        r"(?:\n\s*\d+(?:\.\d+)*\.?\s+|"
        r"\b(?:thời\s+hạn\s+tù|được\s+trừ|đã\s+chấp\s+hành|"
        r"hình\s+ph(?:ạt|át)\s+bổ\s+sung|trả\s+tự\s+do)\b)",
        remainder,
        maxsplit=1,
        flags=re.I,
    )[0]
    stripped = remainder.lstrip()
    if not stripped or stripped.startswith((".", ";", "\n")):
        return False
    if re.match(r"^,?\s*tính\s+từ\s+ngày\b", stripped, re.I):
        return False
    return bool(
        re.match(r"^,\s*\d{1,3}(?!\s*(?:năm|tháng|ngày)\b)", stripped, re.I)
        or re.match(r"^(?:,\s*)?và(?:\s*\.{2,}|\s*$)", stripped, re.I)
        or re.match(r"^,\s*$", stripped)
    )


def _evidence_span_is_consistent(
    raw_text: str,
    line_ids: list[str],
    clause_spans: list[Mapping[str, Any]],
) -> bool:
    if not clause_spans or len(line_ids) != len(set(line_ids)):
        return False
    if line_ids != list(
        dict.fromkeys(_text(span.get("line_id")) for span in clause_spans)
    ):
        return False
    rebuilt: list[str] = []
    for span in clause_spans:
        raw_line = str(span.get("raw_line_text") or "")
        start = _optional_int(span.get("char_start"))
        end = _optional_int(span.get("char_end"))
        raw_clause = str(span.get("raw_clause") or "")
        if start is None or end is None or start < 0 or end < start:
            return False
        if raw_line[start:end] != raw_clause:
            return False
        rebuilt.append(raw_clause)
    return raw_text == "\n".join(rebuilt)


def _validate_sentence_aggregates(
    sentence_map: dict[str, dict[str, Any]],
    evidence: list[dict[str, Any]],
    warnings: list[str],
    warning_records: list[dict[str, Any]],
    *,
    defendants: list[dict[str, Any]],
    case_id: str,
) -> None:
    warning_types = {
        "sentence_start_anchor_unparsed": "sentence_start",
        "probation_duration_partial": "probation",
        "probation_start_unparsed": "probation",
        "detention_credit_anchor_unparsed": "detention_credit",
        "completion_anchor_unparsed": "completion",
        "additional_penalty_anchor_unparsed": "additional_penalty",
    }
    for entity_id, sentence in sentence_map.items():
        entity_evidence = [
            item
            for item in evidence
            if entity_id in item.get("defendant_entity_ids", [])
        ]
        authoritative_text = "\n".join(
            str(item.get("raw_clause") or item.get("raw_text") or "")
            for item in entity_evidence
            if str(item.get("raw_clause") or item.get("raw_text") or "").strip()
        )
        final_warnings = _sentence_completeness_warnings(
            authoritative_text, sentence
        )
        sentence["warnings"] = [
            warning
            for warning in sentence.get("warnings", [])
            if warning not in SENTENCE_COMPLETENESS_WARNINGS
        ]
        for warning in final_warnings:
            evidence_type = warning_types.get(warning)
            source = next(
                (
                    item
                    for item in entity_evidence
                    if item.get("evidence_type") == evidence_type
                ),
                entity_evidence[0] if entity_evidence else {},
            )
            source["warnings"] = list(
                dict.fromkeys([*source.get("warnings", []), warning])
            )
            sentence["warnings"].append(warning)
            warnings.append(warning)
            warning_records.append(
                _sentence_warning_record(
                    case_id=case_id,
                    warning=warning,
                    scope="entity",
                    defendant_entity_id=entity_id,
                    defendant_name=_defendant_name(entity_id, defendants),
                    page_number=_optional_int(source.get("page_number")),
                    line_ids=list(source.get("line_ids", [])),
                    raw_text=str(
                        source.get("raw_clause") or source.get("raw_text") or ""
                    ),
                )
            )
        sentence["warnings"] = list(dict.fromkeys(sentence["warnings"]))

    for item in evidence:
        if item.get("defendant_entity_ids"):
            continue
        final_warnings = _sentence_completeness_warnings(
            str(item.get("raw_clause") or item.get("raw_text") or ""), item
        )
        for warning in final_warnings:
            item["warnings"] = list(
                dict.fromkeys([*item.get("warnings", []), warning])
            )
            warnings.append(warning)
            warning_records.append(
                _sentence_warning_record(
                    case_id=case_id,
                    warning=warning,
                    scope="case",
                    defendant_entity_id="",
                    defendant_name="",
                    page_number=_optional_int(item.get("page_number")),
                    line_ids=list(item.get("line_ids", [])),
                    raw_text=str(
                        item.get("raw_clause") or item.get("raw_text") or ""
                    ),
                )
            )


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


def _authoritative_sentence_input(
    lines_or_text: str | list[dict[str, Any]],
) -> str | list[dict[str, Any]]:
    if isinstance(lines_or_text, str):
        kept: list[str] = []
        for line in lines_or_text.splitlines():
            if _is_administrative_tail_line(line):
                break
            kept.append(line)
        return "\n".join(kept)
    kept_lines: list[dict[str, Any]] = []
    for line in lines_or_text:
        if _is_administrative_tail_line(str(line.get("text") or "")):
            break
        kept_lines.append(line)
    return kept_lines


def _is_administrative_tail_line(value: str) -> bool:
    folded = fold_text(value)
    return any(marker in folded for marker in _ADMINISTRATIVE_TAIL_MARKERS)


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
        "sentence_warnings": [],
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
