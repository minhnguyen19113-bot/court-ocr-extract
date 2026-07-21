from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from collections.abc import Mapping
from typing import Any, Iterable


FRONT_PRE_CONTENT = "front_pre_content"
DECISION_TAIL = "decision_tail"
MIDDLE_EXCLUDED = "middle_excluded"

ALLOWED_PRODUCTION_SOURCE_REGIONS = frozenset(
    {FRONT_PRE_CONTENT, DECISION_TAIL}
)
MIDDLE_EXCLUDED_HEADINGS = frozenset(
    {
        "NỘI DUNG VỤ ÁN",
        "NHẬN ĐỊNH CỦA TÒA ÁN",
    }
)

FRONT_PRE_CONTENT_FINAL_FIELDS = frozenset(
    {
        "LOẠI ÁN",
        "SỐ THỤ LÝ",
        "NGÀY THỤ LÝ",
        "NGÀY THỤ LÝ (DD/MM/YYYY)",
        "TƯ CÁCH TỐ TỤNG",
        "HỌ TÊN ĐƯƠNG SỰ",
        "NĂM SINH",
        "CCCD",
        "ĐỊA CHỈ",
        "HỌ TÊN CHỦ TỌA",
    }
)
DECISION_TAIL_FIELDS = frozenset(
    {
        "TỘI DANH",
        "QUAN HỆ PHÁP LUẬT",
        "HÌNH PHẠT",
        "MỨC HÌNH PHẠT",
        "ÁN TREO",
        "THỜI GIAN THỬ THÁCH",
        "TRÁCH NHIỆM DÂN SỰ ĐƯỢC TUYÊN",
        "XỬ LÝ VẬT CHỨNG",
        "ÁN PHÍ",
    }
)

_FRONT_TECHNICAL_FIELDS = frozenset(
    {
        "metadata.case_type",
        "metadata.case_acceptance_number",
        "metadata.case_acceptance_date",
        "trial_panel.presiding_judge",
        "defendant.role",
        "defendant.full_name",
        "defendant.birth_date_or_year",
        "defendant.cccd",
        "defendant.address",
        "participant.role",
        "participant.full_name",
        "participant.birth_date_or_year",
        "participant.cccd",
        "participant.address",
    }
)
_DECISION_TECHNICAL_FIELDS = frozenset(
    {
        "case_charges",
        "defendant_charge_map",
        "charge_output.case_charges",
        "charge_output.defendant_charge_map",
        "defendant_sentence_map",
        "sentence_output.defendant_sentence_map",
        "metadata.legal_relationship",
    }
)


@dataclass(frozen=True)
class SourceRegionAudit:
    field_name: str
    source_region: str
    source_page: int | None
    evidence_line_ids: list[str]
    allowed: bool
    warning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def allowed_source_regions(field_name: object) -> frozenset[str]:
    value = _clean(field_name)
    display = value.upper()
    if display in FRONT_PRE_CONTENT_FINAL_FIELDS or value in _FRONT_TECHNICAL_FIELDS:
        return frozenset({FRONT_PRE_CONTENT})
    if display in DECISION_TAIL_FIELDS or value in _DECISION_TECHNICAL_FIELDS:
        return frozenset({DECISION_TAIL})
    return frozenset()


def is_source_region_allowed(field_name: object, source_region: object) -> bool:
    region = _clean(source_region)
    return (
        region in ALLOWED_PRODUCTION_SOURCE_REGIONS
        and region in allowed_source_regions(field_name)
    )


def audit_source_region(
    field_name: object,
    source_region: object,
    *,
    source_page: int | None = None,
    evidence_line_ids: Iterable[object] = (),
) -> dict[str, Any]:
    field = _clean(field_name)
    region = _clean(source_region)
    line_ids = list(
        dict.fromkeys(_clean(value) for value in evidence_line_ids if _clean(value))
    )
    page = source_page if source_page is not None else source_page_from_line_ids(line_ids)
    allowed_regions = allowed_source_regions(field)
    allowed = is_source_region_allowed(field, region)
    if region == MIDDLE_EXCLUDED:
        warning = "middle_source_region_is_excluded"
    elif region not in ALLOWED_PRODUCTION_SOURCE_REGIONS:
        warning = "source_region_not_allowed_in_production"
    elif not allowed_regions:
        warning = "field_source_contract_missing"
    elif not allowed:
        warning = "field_source_region_mismatch"
    else:
        warning = ""
    return SourceRegionAudit(
        field_name=field,
        source_region=region,
        source_page=page,
        evidence_line_ids=line_ids,
        allowed=allowed,
        warning=warning,
    ).to_dict()


def build_extraction_source_region_audit(
    extraction_result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int | None, tuple[str, ...]]] = set()

    for evidence in _mapping_items(extraction_result.get("evidence")):
        field_name = _clean(evidence.get("field"))
        if not allowed_source_regions(field_name):
            continue
        source_region = _clean(evidence.get("source_region")) or (
            DECISION_TAIL
            if _clean(evidence.get("source")) == "decision_tail_charge"
            else FRONT_PRE_CONTENT
        )
        line_ids = _line_ids_from_evidence(evidence)
        _append_audit(
            rows,
            seen,
            audit_source_region(
                field_name,
                source_region,
                source_page=_optional_int(evidence.get("page_number")),
                evidence_line_ids=line_ids,
            ),
        )

    metadata = extraction_result.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    if metadata.get("case_type"):
        _append_audit(
            rows,
            seen,
            audit_source_region("LOẠI ÁN", FRONT_PRE_CONTENT),
        )

    trial_panel = extraction_result.get("trial_panel")
    trial_panel = trial_panel if isinstance(trial_panel, Mapping) else {}
    if trial_panel.get("presiding_judge"):
        _append_audit(
            rows,
            seen,
            audit_source_region("HỌ TÊN CHỦ TỌA", FRONT_PRE_CONTENT),
        )

    for group_name, field_prefix in (
        ("defendants", "defendant"),
        ("participants", "participant"),
    ):
        values = extraction_result.get(group_name)
        for entity in values if isinstance(values, list) else []:
            if not isinstance(entity, Mapping):
                continue
            line_ids = entity.get("evidence_line_ids")
            line_ids = line_ids if isinstance(line_ids, list) else []
            source_region = _clean(entity.get("source_region")) or FRONT_PRE_CONTENT
            field_values = (
                (f"{field_prefix}.role", "Bị cáo" if group_name == "defendants" else entity.get("role")),
                (f"{field_prefix}.full_name", entity.get("full_name")),
                (f"{field_prefix}.birth_date_or_year", entity.get("birth_date_or_year")),
                (f"{field_prefix}.cccd", entity.get("cccd")),
                (
                    f"{field_prefix}.address",
                    entity.get("current_address")
                    or entity.get("permanent_address")
                    or entity.get("address"),
                ),
            )
            for field_name, value in field_values:
                if value in (None, ""):
                    continue
                _append_audit(
                    rows,
                    seen,
                    audit_source_region(
                        field_name,
                        source_region,
                        evidence_line_ids=line_ids,
                    ),
                )

    charge_output = extraction_result.get("charge_output")
    charge_output = charge_output if isinstance(charge_output, Mapping) else {}
    charge_evidence = charge_output.get("charge_evidence")
    for evidence in charge_evidence if isinstance(charge_evidence, list) else []:
        if not isinstance(evidence, Mapping):
            continue
        _append_audit(
            rows,
            seen,
            audit_source_region(
                "QUAN HỆ PHÁP LUẬT",
                evidence.get("source_region") or DECISION_TAIL,
                source_page=_optional_int(evidence.get("page_number")),
                evidence_line_ids=evidence.get("line_ids") or [],
            ),
        )
    sentence_output = extraction_result.get("sentence_output")
    sentence_output = sentence_output if isinstance(sentence_output, Mapping) else {}
    sentence_evidence = sentence_output.get("sentence_evidence")
    for evidence in sentence_evidence if isinstance(sentence_evidence, list) else []:
        if not isinstance(evidence, Mapping):
            continue
        _append_audit(
            rows,
            seen,
            audit_source_region(
                "HÌNH PHẠT",
                evidence.get("source_region") or DECISION_TAIL,
                source_page=_optional_int(evidence.get("page_number")),
                evidence_line_ids=evidence.get("line_ids") or [],
            ),
        )
    return rows


def source_page_from_line_ids(line_ids: Iterable[object]) -> int | None:
    for value in line_ids:
        match = re.match(r"p(\d{1,6})_", _clean(value), re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _append_audit(
    rows: list[dict[str, Any]],
    seen: set[tuple[str, str, int | None, tuple[str, ...]]],
    row: dict[str, Any],
) -> None:
    key = (
        str(row["field_name"]),
        str(row["source_region"]),
        row.get("source_page"),
        tuple(str(value) for value in row.get("evidence_line_ids", [])),
    )
    if key not in seen:
        seen.add(key)
        rows.append(row)


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _line_ids_from_evidence(evidence: Mapping[str, Any]) -> list[str]:
    values = evidence.get("line_ids")
    if isinstance(values, list):
        return [_clean(value) for value in values if _clean(value)]
    line_id = _clean(evidence.get("line_id"))
    return [line_id] if line_id else []


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
