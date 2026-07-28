from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from court_ocr_extract.domain.form_engine import (
    CapabilityStatus,
    FormEngineCapabilities,
    GenerationMode,
    GenerationRequest,
    GenerationResult,
    GenerationSource,
    get_form_engine_capabilities,
)


class FormGenerationViolationCode(str, Enum):
    OFFICIAL_SOURCE_NOT_APPROVED_OR_PUBLISHED = (
        "OFFICIAL_SOURCE_NOT_APPROVED_OR_PUBLISHED"
    )
    APPROVED_SNAPSHOT_NOT_LOCKED = "APPROVED_SNAPSHOT_NOT_LOCKED"
    DRAFT_PREVIEW_UNSUPPORTED = "DRAFT_PREVIEW_UNSUPPORTED"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"


@dataclass(frozen=True)
class FormGenerationValidation:
    violation_codes: tuple[FormGenerationViolationCode, ...]

    @property
    def allowed(self) -> bool:
        return not self.violation_codes


class FormGenerationRejected(ValueError):
    def __init__(self, validation: FormGenerationValidation) -> None:
        self.validation = validation
        self.violation_codes = validation.violation_codes
        codes = ", ".join(code.value for code in validation.violation_codes)
        super().__init__(f"Form generation request rejected: {codes}")


class FormService:
    def capabilities(self) -> FormEngineCapabilities:
        return get_form_engine_capabilities()

    def validate(self, request: GenerationRequest) -> FormGenerationValidation:
        violations: list[FormGenerationViolationCode] = []

        if request.mode is GenerationMode.PREVIEW:
            violations.append(FormGenerationViolationCode.DRAFT_PREVIEW_UNSUPPORTED)
        elif request.source not in {
            GenerationSource.APPROVED_SNAPSHOT,
            GenerationSource.PUBLISHED_CORE,
        }:
            violations.append(
                FormGenerationViolationCode.OFFICIAL_SOURCE_NOT_APPROVED_OR_PUBLISHED
            )

        if (
            request.source is GenerationSource.APPROVED_SNAPSHOT
            and not request.source_is_locked
        ):
            violations.append(
                FormGenerationViolationCode.APPROVED_SNAPSHOT_NOT_LOCKED
            )

        format_capability = self.capabilities().for_format(request.output_format)
        if (
            not format_capability.adapter_implemented
            or format_capability.capability_status is not CapabilityStatus.AVAILABLE
        ):
            violations.append(FormGenerationViolationCode.ADAPTER_UNAVAILABLE)

        return FormGenerationValidation(tuple(dict.fromkeys(violations)))

    def generate(self, request: GenerationRequest) -> GenerationResult:
        validation = self.validate(request)
        if not validation.allowed:
            raise FormGenerationRejected(validation)

        # No adapter is AVAILABLE in Phase 0. This guard stays fail-closed if the
        # capability matrix and implementation registry diverge in a later phase.
        raise FormGenerationRejected(
            FormGenerationValidation(
                (FormGenerationViolationCode.ADAPTER_UNAVAILABLE,)
            )
        )

