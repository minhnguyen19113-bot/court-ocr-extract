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
DEFAULT_VERDICT_BLOCK_MAX_LINES = 10
DEFAULT_VERDICT_BLOCK_MAX_CHARS = 1600

_QUOTE_OPEN = "“\"‘'"
_QUOTE_CLOSE = "”\"’'"
_VERDICT_START_RE = re.compile(
    r"\b(?:(?P<sentence>Xử\s+phạt)|(?P<declare>Tuyên))\s+"
    r"(?:các\s+)?bị\s+cáo\s+|\b(?P<direct>Bị\s+cáo)\s+",
    re.IGNORECASE,
)
_VERDICT_START_FOLDED_RE = re.compile(
    r"(?:^|\s)(?:\d+(?:\.\d+)*[.)]?\s*)?"
    r"(?:(?:xu phat|tuyen)\s+(?:cac\s+)?bi cao|bi cao\s+.+?\s+pham toi)\b",
    re.IGNORECASE,
)
_DECISION_ITEM_RE = re.compile(r"^\s*\d+(?:\.\d+)*[.)]\s*(?:\S.*)?$")
_STANDALONE_PAGE_NUMBER_RE = re.compile(r"^\s*(?:trang\s+)?\d+\s*$", re.IGNORECASE)
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


def iter_verdict_blocks(
    lines_or_text: str | Iterable[Mapping[str, Any]],
    *,
    max_lines: int = DEFAULT_VERDICT_BLOCK_MAX_LINES,
    max_chars: int = DEFAULT_VERDICT_BLOCK_MAX_CHARS,
) -> list[dict[str, Any]]:
    if max_lines < 1 or max_chars < 1:
        raise ValueError("verdict block guards must be positive")

    lines = _ordered_lines(_coerce_lines(lines_or_text))
    blocks: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        if not _is_verdict_start(_text(lines[index].get("text"))):
            index += 1
            continue

        block_lines: list[dict[str, Any]] = []
        char_count = 0
        cursor = index
        while cursor < len(lines) and len(block_lines) < max_lines:
            line = lines[cursor]
            text = _text(line.get("text"))
            if cursor > index:
                current_text = "\n".join(
                    _text(item.get("text")) for item in block_lines
                )
                if _is_verdict_start(text):
                    break
                if _is_strong_item_boundary(text) and _block_has_charge(current_text):
                    break
            cursor += 1
            if not text or _is_standalone_page_number(text):
                continue
            added = len(text) + (1 if block_lines else 0)
            if block_lines and char_count + added > max_chars:
                break
            block_lines.append(line)
            char_count += added

        if block_lines:
            raw_text = "\n".join(
                _text(item.get("text")) for item in block_lines
            )
            blocks.append(
                {
                    "raw_text": raw_text,
                    "line_ids": [
                        _text(item.get("line_id"))
                        for item in block_lines
                        if _text(item.get("line_id"))
                    ],
                    "page_number": next(
                        (
                            _optional_int(item.get("page_number"))
                            for item in block_lines
                            if _optional_int(item.get("page_number")) is not None
                        ),
                        None,
                    ),
                    "line_count": len(block_lines),
                }
            )
        index = max(cursor, index + 1)
    return blocks


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
    decision_lines = [
        line
        for line in lines
        if _text(line.get("source_region")) in {"", DECISION_TAIL}
    ]
    blocks = iter_verdict_blocks(decision_lines)
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

    for block in blocks:
        text = _text(block.get("raw_text"))
        start = _VERDICT_START_RE.search(text)
        if not start:
            continue
        base_name = _verdict_base_name(start)
        anchor = _find_charge_anchor(text, start.end(), base_name)
        if not anchor:
            continue
        charge, quoted = _charge_after_anchor(text[anchor.end():])
        if not charge:
            continue

        names_scope = text[start.end():anchor.start()]
        name_match = _match_defendant_entities(
            names_scope,
            refs,
            pattern_name=base_name,
            min_score=float(min_name_match_score),
            ambiguity_gap=float(name_match_ambiguity_gap),
        )
        if name_match.warning:
            warnings.append(name_match.warning)

        line_ids = tuple(
            _text(value) for value in block.get("line_ids", []) if _text(value)
        )
        evidence_key = (
            charge.casefold(),
            tuple(name_match.entity_ids),
            line_ids or (str(len(evidence)),),
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
                page_number=_optional_int(block.get("page_number")),
                line_ids=list(line_ids),
                raw_text=text,
                match_method=(
                    f"{base_name}_{'quoted' if quoted else 'unquoted'}:"
                    f"{name_match.method}"
                ),
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
    normalized_scope = fold_text(names_clause)
    display_candidate = _clean(names_clause)
    if any(marker in normalized_scope for marker in _COLLECTIVE_UNRESOLVED_MARKERS):
        return _NameMatch(
            [],
            [display_candidate] if display_candidate else [],
            "unresolved_collective",
            "unresolved_collective_defendant_charge_mapping",
        )

    exact_matches = _exact_name_matches(normalized_scope, refs)
    if exact_matches:
        matched_refs = [item[0] for item in exact_matches]
        methods = list(dict.fromkeys(item[1] for item in exact_matches))
        return _NameMatch(
            [item.entity_id for item in matched_refs],
            [item.full_name for item in matched_refs],
            "+".join(methods),
            "",
        )

    candidate = _candidate_name_text(names_clause, pattern_name)
    normalized_candidate = fold_text(candidate)
    display_candidate = _clean(candidate)
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
        if any(
            start < chosen_end and end > chosen_start
            for chosen_start, chosen_end, *_ in selected
        ):
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
        refs.append(
            _DefendantRef(
                entity_id=entity_id,
                full_name=full_name,
                normalized_name=normalized,
                normalized_without_honorific=fold_text(
                    _HONORIFIC_PREFIX_RE.sub("", full_name)
                ),
            )
        )
    return refs


def _candidate_name_text(value: str, pattern_name: str) -> str:
    candidate = re.sub(r"\s+", " ", value).strip(" ,;:-")
    if pattern_name == "sentence_for_charge":
        candidate = re.split(
            r"\s+(?:(?:bị|phạt)\s+)?\d+\b"
            r"|\s+(?:mức\s+án|hình\s+phạt|mỗi\s+bị\s+cáo)\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
    return candidate.strip(" ,;:-")


def _verdict_base_name(match: re.Match[str]) -> str:
    if match.group("sentence"):
        return "sentence_for_charge"
    if match.group("declare"):
        return "declare_guilty"
    return "defendant_guilty"


def _find_charge_anchor(
    text: str,
    start: int,
    base_name: str,
) -> re.Match[str] | None:
    anchor = r"về\s+tội" if base_name == "sentence_for_charge" else r"phạm\s+tội"
    return re.compile(rf"\b{anchor}\b", re.IGNORECASE).search(text, pos=start)


def _charge_after_anchor(value: str) -> tuple[str, bool]:
    tail = value.lstrip()
    if not tail:
        return "", False
    if tail[0] in _QUOTE_OPEN:
        quoted = re.match(
            rf"^[{re.escape(_QUOTE_OPEN)}]\s*"
            rf"(?P<charge>[^{re.escape(_QUOTE_CLOSE)}]{{2,200}}?)\s*"
            rf"[{re.escape(_QUOTE_CLOSE)}]",
            tail,
            re.DOTALL,
        )
        return (_normalize_charge(quoted.group("charge")), True) if quoted else ("", True)
    unquoted = re.match(
        r"^(?P<charge>[^\n.;]{2,200}?)"
        r"(?=\s*(?:[.;\n]|$|,?\s*\b(?:theo|quy\s+định\s+tại|căn\s+cứ)\b))",
        tail,
        re.IGNORECASE,
    )
    return (_normalize_charge(unquoted.group("charge")), False) if unquoted else ("", False)


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


def _block_has_charge(text: str) -> bool:
    start = _VERDICT_START_RE.search(text)
    if not start:
        return False
    base_name = _verdict_base_name(start)
    anchor = _find_charge_anchor(text, start.end(), base_name)
    return bool(anchor and _charge_after_anchor(text[anchor.end():])[0])


def _is_verdict_start(text: str) -> bool:
    return bool(_VERDICT_START_FOLDED_RE.search(fold_text(text)))


def _is_strong_item_boundary(text: str) -> bool:
    return bool(_DECISION_ITEM_RE.match(text))


def _is_standalone_page_number(text: str) -> bool:
    return bool(_STANDALONE_PAGE_NUMBER_RE.match(fold_text(text)))


def _ordered_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed = list(enumerate(lines))
    indexed.sort(
        key=lambda item: (
            _optional_int(item[1].get("page_number")) or 0,
            _optional_int(item[1].get("reading_order"))
            if _optional_int(item[1].get("reading_order")) is not None
            else item[0],
            item[0],
        )
    )
    return [dict(line) for _, line in indexed]


def _coerce_lines(
    lines_or_text: str | Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(lines_or_text, str):
        return [
            {
                "line_id": f"decision_l{index:04d}",
                "source_region": DECISION_TAIL,
                "reading_order": index - 1,
                "text": text,
            }
            for index, text in enumerate(lines_or_text.splitlines(), start=1)
            if text.strip()
        ]
    return [dict(line) for line in lines_or_text if isinstance(line, Mapping)]


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio() * 100.0


def _optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


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
