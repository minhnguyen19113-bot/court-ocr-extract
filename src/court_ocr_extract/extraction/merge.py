from __future__ import annotations

import re
import unicodedata

from court_ocr_extract.extraction.schemas import CASE_FIELD_KEYS, PARTICIPANT_FIELD_KEYS
from court_ocr_extract.models import CaseInfo, ExtractionResult, ExtractorOutput, Participant, model_to_dict


def merge_extractor_outputs(
    *,
    source_file: str | None,
    text_before_marker: str,
    marker_found: bool,
    marker_text: str | None,
    marker_page: int | None,
    primary: ExtractorOutput,
    support: ExtractorOutput | None = None,
    warnings: list[str] | None = None,
) -> ExtractionResult:
    conflict_warnings: list[str] = []
    case_values = {}
    case_meta = {}
    for key in CASE_FIELD_KEYS:
        selected = _select_field(
            primary.case_fields.get(key),
            support.case_fields.get(key) if support else None,
            field_key=key,
            warnings=conflict_warnings,
        )
        case_values[key] = selected.value if selected else None
        if selected:
            case_meta[key] = selected

    participants = []
    max_count = max(len(primary.participants), len(support.participants) if support else 0)
    for index in range(max_count):
        primary_item = primary.participants[index] if index < len(primary.participants) else {}
        support_item = support.participants[index] if support and index < len(support.participants) else {}
        values = {}
        metadata = {}
        for key in PARTICIPANT_FIELD_KEYS:
            selected = _select_field(
                primary_item.get(key),
                support_item.get(key),
                field_key=f"participants[{index}].{key}",
                warnings=conflict_warnings,
            )
            values[key] = selected.value if selected else None
            if selected:
                metadata[key] = selected
        participants.append(Participant(**values, field_metadata=metadata))

    merged_warnings = []
    warning_groups = [
        warnings or [],
        conflict_warnings,
        primary.warnings,
        support.warnings if support else [],
    ]
    for group in warning_groups:
        for item in group:
            if item and item not in merged_warnings:
                merged_warnings.append(item)

    return ExtractionResult(
        source_file=source_file,
        marker_found=marker_found,
        marker_text=marker_text,
        marker_page=marker_page,
        text_before_marker=text_before_marker,
        case_info=CaseInfo(**case_values, field_metadata=case_meta),
        participants=participants,
        warnings=merged_warnings,
        metadata={
            "primary_extractor": primary.method,
            "support_extractor": support.method if support else None,
        },
        raw_extractor_outputs={
            primary.method: model_to_dict(primary),
            **({support.method: model_to_dict(support)} if support else {}),
        },
    )


def _select_field(primary, support, *, field_key: str, warnings: list[str]):
    primary_has_value = bool(primary and primary.value not in (None, ""))
    support_has_value = bool(support and support.value not in (None, ""))

    if primary_has_value and support_has_value:
        primary_key = _normalized_value(primary.value)
        support_key = _normalized_value(support.value)
        if primary_key and support_key and primary_key != support_key:
            selected = _higher_confidence(primary, support)
            warnings.append(
                "Conflict giữa extractor ở field "
                f"{field_key}; chọn {selected.source_method or 'unknown'} theo confidence."
            )
            return selected
        return primary

    if primary_has_value:
        return primary
    if support_has_value:
        return support
    return primary or support


def _higher_confidence(primary, support):
    primary_confidence = primary.confidence if primary.confidence is not None else 0.0
    support_confidence = support.confidence if support.confidence is not None else 0.0
    return support if support_confidence > primary_confidence else primary


def _normalized_value(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", str(value).casefold())
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"\W+", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()
