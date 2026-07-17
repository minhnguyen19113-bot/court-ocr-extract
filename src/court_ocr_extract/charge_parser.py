from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any

from court_ocr_extract.extractors.pre_content_anchor_segmenter import fold_text
from court_ocr_extract.source_region_policy import DECISION_TAIL


DEFAULT_NAME_MATCH_MIN_SCORE = 88.0
DEFAULT_NAME_MATCH_AMBIGUITY_GAP = 5.0

_QUOTE_OPEN = "“\"‘'"
_QUOTE_CLOSE = "”\"’'"
_QUOTED_CHARGE = (
    rf"[{re.escape(_QUOTE_OPEN)}]\s*"
    rf"(?P<charge>[^{re.escape(_QUOTE_CLOSE)}]{{2,200}}?)\s*"
    rf"[{re.escape(_QUOTE_CLOSE)}]"
)
_UNQUOTED_CHARGE = (
    r"(?P<charge>[^\n.;]{2,200}?)"
    r"(?=\s*(?:[.;\n]|$|,?\s*\b(?:theo|quy\s+định\s+tại|căn\s+cứ)\b))"
)
_VERDICT_BASES = (
    (
        "declare_guilty",
        r"\bTuyên\s+(?:các\s+)?bị\s+cáo\s+(?P<names>.{1,300}?)"
        r"\s+phạm\s+tội\s*",
    ),
    (
        "sentence_for_charge",
        r"\bXử\s+phạt\s+(?:các\s+)?bị\s+cáo\s+(?P<names>.{1,400}?)"
        r"\s+về\s+tội\s*",
    ),
    (
        "defendant_guilty",
        r"\bBị\s+cáo\s+(?P<names>.{1,300}?)\s+phạm\s+tội\s*",
    ),
)
_VERDICT_PATTERNS = tuple(
    (
        f"{base_name}_{suffix}",
        re.compile(base + charge_pattern, re.IGNORECASE | re.DOTALL),
        base_name,
        quoted,
    )
    for base_name, base in _VERDICT_BASES
    for suffix, charge_pattern, quoted in (
        ("quoted", _QUOTED_CHARGE, True),
        ("unquoted", _UNQUOTED_CHARGE, False),
    )
)
_HONORIFIC_PREFIX_RE = re.compile(
    r"^(?:ông\s+bị\s+cáo|bà\s+bị\s+cáo|bị\s+cáo|ông|bà|anh|chị)\s+",
    re.IGNORECASE,
)
_COLLECTIVE_UNRESOLVED_MARKERS = (
    "con lai",
    "cac bi cao khac",
    "nhung bi cao con lai",
)


@dataclass(frozen=True)
class ChargeEvidence:
    charge: str
    defendant_entity_ids: list[str]
    defendant_names: list[str]
    source_region: str
    page_number: int | None
    line_ids: list[str]
    raw_text: str
    match_method: str
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _DefendantRef:
    entity_id: str
    full_name: str
    normalized_name: str
    normalized_without_honorific: str


@dataclass(frozen=True)
class _NameMatch:
    entity_ids: list[str]
    names: list[str]
    method: str
    warning: str


def parse_explicit_decision_charges(
    lines_or_text: str | Iterable[Mapping[str, Any]],
    *,
    defendants: Iterable[Mapping[str, Any]] = (),
    defendant_names: Iterable[str] = (),
    source_region: str = DECISION_TAIL,
    min_name_match_score: float = DEFAULT_NAME_MATCH_MIN_SCORE,
    name_match_ambiguity_gap: float = DEFAULT_NAME_MATCH_AMBIGUITY_GAP,
) -> dict[str, Any]:
    if source_region != DECISION_TAIL:
        return _empty_result(f"charge_source_region_not_allowed:{source_region}")

    lines = _coerce_lines(lines_or_text)
    excluded_regions = {
        _text(line.get("source_region"))
        for line in lines
        if _text(line.get("source_region")) not in {"", DECISION_TAIL}
    }
    lines = [
        line
        for line in lines
        if _text(line.get("source_region")) in {"", DECISION_TAIL}
    ]
    refs = _defendant_refs(defendants, defendant_names)
    charges: list[str] = []
    charge_keys: set[str] = set()
    defendant_charge_map: dict[str, list[str]] = {}
    evidence: list[ChargeEvidence] = []
    warnings = [
        f"charge_lines_ignored_from_source_region:{region}"
        for region in sorted(excluded_regions)
    ]
    seen_evidence: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()

    for start in range(len(lines)):
        window = lines[start:start + 3]
        text, line_spans = _window_text_and_spans(window)
        if not text:
            continue
        for pattern_name, pattern, base_name, quoted in _VERDICT_PATTERNS:
            for match in pattern.finditer(text):
                charge = _normalize_charge(match.group("charge"))
                if not charge:
                    continue
                name_match = _match_defendant_entities(
                    match.group("names"),
                    refs,
                    pattern_name=base_name,
                    min_score=float(min_name_match_score),
                    ambiguity_gap=float(name_match_ambiguity_gap),
                )
                if name_match.warning:
                    warnings.append(name_match.warning)
                matched_spans = [
                    span
                    for span in line_spans
                    if span[0] < match.end() and span[1] > match.start()
                ]
                line_ids = tuple(span[2] for span in matched_spans if span[2])
                evidence_key = (
                    charge.casefold(),
                    tuple(name_match.entity_ids),
                    line_ids or (str(start),),
                )
                if evidence_key in seen_evidence:
                    continue
                seen_evidence.add(evidence_key)

                charge_key = charge.casefold()
                if charge_key not in charge_keys:
                    charge_keys.add(charge_key)
                    charges.append(charge)
                for entity_id in name_match.entity_ids:
                    mapped = defendant_charge_map.setdefault(entity_id, [])
                    if charge not in mapped:
                        mapped.append(charge)

                page_number = next(
                    (span[3] for span in matched_spans if span[3] is not None),
                    None,
                )
                confidence = (
                    "high"
                    if quoted and name_match.entity_ids
                    else "medium"
                    if quoted or name_match.entity_ids
                    else "low"
                )
                evidence.append(
                    ChargeEvidence(
                        charge=charge,
                        defendant_entity_ids=list(name_match.entity_ids),
                        defendant_names=list(name_match.names),
                        source_region=DECISION_TAIL,
                        page_number=page_number,
                        line_ids=list(line_ids),
                        raw_text=match.group(0).strip(),
                        match_method=f"{pattern_name}:{name_match.method}",
                        confidence=confidence,
                    )
                )

    return {
        "case_charges": charges,
        "defendant_charge_map": defendant_charge_map,
        "charge_evidence": [item.to_dict() for item in evidence],
        "warnings": list(dict.fromkeys(warnings)),
    }


def _match_defendant_entities(
    names_clause: str,
    refs: list[_DefendantRef],
    *,
    pattern_name: str,
    min_score: float,
    ambiguity_gap: float,
) -> _NameMatch:
    candidate = _candidate_name_text(names_clause, pattern_name)
    normalized_candidate = fold_text(candidate)
    display_candidate = _clean(candidate)
    if any(marker in normalized_candidate for marker in _COLLECTIVE_UNRESOLVED_MARKERS):
        return _NameMatch(
            [],
            [display_candidate] if display_candidate else [],
            "unresolved_collective",
            "unresolved_collective_defendant_charge_mapping",
        )

    exact_matches = _exact_name_matches(normalized_candidate, refs)
    if exact_matches:
        matched_refs = [item[0] for item in exact_matches]
        methods = list(dict.fromkeys(item[1] for item in exact_matches))
        return _NameMatch(
            [item.entity_id for item in matched_refs],
            [item.full_name for item in matched_refs],
            "+".join(methods),
            "",
        )

    if not refs or not normalized_candidate:
        return _NameMatch(
            [],
            [display_candidate] if display_candidate else [],
            "unmapped",
            "unmatched_defendant_charge_mapping",
        )

    scored = sorted(
        [
            (
                max(
                    _similarity(normalized_candidate, ref.normalized_name),
                    _similarity(
                        normalized_candidate,
                        ref.normalized_without_honorific,
                    ),
                ),
                index,
                ref,
            )
            for index, ref in enumerate(refs)
        ],
        key=lambda item: item[0],
        reverse=True,
    )
    top_score, _, top_ref = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    if top_score < min_score:
        return _NameMatch(
            [],
            [display_candidate] if display_candidate else [],
            "unmapped",
            "unmatched_defendant_charge_mapping",
        )
    eligible = [item for item in scored if item[0] >= min_score]
    if len(eligible) != 1 or (
        len(scored) > 1 and top_score - second_score < ambiguity_gap
    ):
        return _NameMatch(
            [],
            [display_candidate] if display_candidate else [],
            "ambiguous_fuzzy",
            "ambiguous_defendant_charge_mapping",
        )
    return _NameMatch(
        [top_ref.entity_id],
        [top_ref.full_name],
        "unique_fuzzy_name",
        "",
    )


def _exact_name_matches(
    normalized_clause: str,
    refs: list[_DefendantRef],
) -> list[tuple[_DefendantRef, str]]:
    candidates: list[tuple[int, int, _DefendantRef, str]] = []
    for ref in refs:
        for value, method in (
            (ref.normalized_name, "exact_normalized_full_name"),
            (
                ref.normalized_without_honorific,
                "exact_normalized_without_honorific",
            ),
        ):
            if not value:
                continue
            match = re.search(rf"(?<!\w){re.escape(value)}(?!\w)", normalized_clause)
            if match:
                candidates.append((match.start(), match.end(), ref, method))

    selected: list[tuple[int, int, _DefendantRef, str]] = []
    selected_ids: set[str] = set()
    for start, end, ref, method in sorted(
        candidates,
        key=lambda item: (-(item[1] - item[0]), item[0]),
    ):
        if ref.entity_id in selected_ids:
            continue
        if any(start < chosen_end and end > chosen_start for chosen_start, chosen_end, *_ in selected):
            continue
        selected.append((start, end, ref, method))
        selected_ids.add(ref.entity_id)
    selected.sort(key=lambda item: item[0])
    return [(item[2], item[3]) for item in selected]


def _defendant_refs(
    defendants: Iterable[Mapping[str, Any]],
    defendant_names: Iterable[str],
) -> list[_DefendantRef]:
    values = [dict(item) for item in defendants if isinstance(item, Mapping)]
    if not values:
        values = [
            {"entity_id": f"defendant_{index:03d}", "full_name": name}
            for index, name in enumerate(defendant_names, start=1)
            if _clean(name)
        ]
    refs: list[_DefendantRef] = []
    seen: set[str] = set()
    for index, item in enumerate(values, start=1):
        full_name = _clean(item.get("full_name"))
        if not full_name:
            continue
        entity_id = _clean(
            item.get("entity_id")
            or item.get("source_block_id")
            or f"defendant_{index:03d}"
        )
        if entity_id in seen:
            continue
        seen.add(entity_id)
        normalized = fold_text(full_name)
        without_honorific = fold_text(_HONORIFIC_PREFIX_RE.sub("", full_name))
        refs.append(
            _DefendantRef(
                entity_id=entity_id,
                full_name=full_name,
                normalized_name=normalized,
                normalized_without_honorific=without_honorific,
            )
        )
    return refs


def _candidate_name_text(value: str, pattern_name: str) -> str:
    candidate = re.sub(r"\s+", " ", value).strip(" ,;:-")
    if pattern_name == "sentence_for_charge":
        candidate = re.split(
            r"\s+(?:(?:bị|phạt)\s+)?\d+\b|\s+mức\s+án\b|\s+hình\s+phạt\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
    return candidate.strip(" ,;:-")


def _normalize_charge(value: object) -> str:
    charge = re.sub(r"\s+", " ", str(value or "")).strip()
    charge = charge.strip(" “”“\"‘’'.,;:-")
    charge = re.split(
        r"\s+(?=(?:theo|quy\s+định\s+tại|căn\s+cứ)\b)",
        charge,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip(" ,;:-")
    if fold_text(charge).startswith(("theo ", "quy dinh tai ", "can cu ")):
        return ""
    return charge


def _coerce_lines(
    lines_or_text: str | Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(lines_or_text, str):
        return [
            {
                "line_id": f"decision_l{index:04d}",
                "source_region": DECISION_TAIL,
                "text": text,
            }
            for index, text in enumerate(lines_or_text.splitlines(), start=1)
            if text.strip()
        ]
    return [dict(line) for line in lines_or_text if isinstance(line, Mapping)]


def _window_text_and_spans(
    window: list[dict[str, Any]],
) -> tuple[str, list[tuple[int, int, str, int | None]]]:
    parts: list[str] = []
    spans: list[tuple[int, int, str, int | None]] = []
    cursor = 0
    for line in window:
        value = _text(line.get("text"))
        if not value:
            continue
        if parts:
            cursor += 1
        start = cursor
        parts.append(value)
        cursor += len(value)
        page_value = line.get("page_number")
        page_number = int(page_value) if str(page_value or "").isdigit() else None
        spans.append((start, cursor, _text(line.get("line_id")), page_number))
    return "\n".join(parts), spans


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio() * 100.0


def _empty_result(warning: str = "") -> dict[str, Any]:
    return {
        "case_charges": [],
        "defendant_charge_map": {},
        "charge_evidence": [],
        "warnings": [warning] if warning else [],
    }


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,;:-")


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()
