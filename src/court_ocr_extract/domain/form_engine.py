from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class CapabilityStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    DECLARED = "DECLARED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class TemplateFormat(str, Enum):
    LEGACY_DOC = "legacy_doc"
    DOCX = "docx"
    PDF = "pdf"


class GenerationSource(str, Enum):
    MACHINE_DRAFT = "MACHINE_DRAFT"
    REVIEW_DRAFT = "REVIEW_DRAFT"
    APPROVED_SNAPSHOT = "APPROVED_SNAPSHOT"
    PUBLISHED_CORE = "PUBLISHED_CORE"


class GenerationMode(str, Enum):
    OFFICIAL = "OFFICIAL"
    PREVIEW = "PREVIEW"


@dataclass(frozen=True)
class FormCatalog:
    catalog_id: str
    code: str
    case_domain: str
    status: CapabilityStatus = CapabilityStatus.DECLARED


@dataclass(frozen=True)
class FormTemplate:
    template_id: str
    catalog_id: str
    code: str
    status: CapabilityStatus = CapabilityStatus.DECLARED


@dataclass(frozen=True)
class FormTemplateVersion:
    template_version_id: str
    template_id: str
    version: int
    template_format: TemplateFormat
    capability_status: CapabilityStatus
    artifact_id: str | None = None
    checksum_sha256: str | None = None


@dataclass(frozen=True)
class ExclusionRule:
    rule_id: str
    target: str
    condition: str | None = None
    validation_rule: str | None = None
    removes_instruction: bool = False


@dataclass(frozen=True)
class FormFieldDefinition:
    field_key: str
    label: str
    data_type: str = "string"
    required: bool = False
    allow_manual_input: bool = False
    default_value: object | None = None
    validation_rule: str | None = None
    help_text: str | None = None


@dataclass(frozen=True)
class FormFieldMapping:
    field_key: str
    source_field: str | None = None
    source_entity: str | None = None
    source_path: str | None = None
    transformation: str | None = None
    formatter: str | None = None
    required: bool = False
    allow_manual_input: bool = False
    default_value: object | None = None
    visibility_condition: str | None = None
    repeat_rule: str | None = None
    exclusion_rule: ExclusionRule | None = None
    validation_rule: str | None = None
    output_placeholder: str | None = None
    instruction_removal_rule: ExclusionRule | None = None


@dataclass(frozen=True)
class FormDefinition:
    definition_id: str
    version: int
    case_domain: str
    template_version_id: str
    fields: tuple[FormFieldDefinition, ...] = ()
    mappings: tuple[FormFieldMapping, ...] = ()
    status: CapabilityStatus = CapabilityStatus.DECLARED


@dataclass(frozen=True)
class ManualField:
    field_key: str
    value: object


@dataclass(frozen=True)
class GenerationRequest:
    request_id: str
    definition_id: str
    definition_version: int
    template_version_id: str
    template_version: int
    source: GenerationSource
    source_id: str
    source_version: int
    output_format: TemplateFormat
    mode: GenerationMode = GenerationMode.OFFICIAL
    source_is_locked: bool = False
    manual_fields: tuple[ManualField, ...] = ()


@dataclass(frozen=True)
class GenerationResult:
    request_id: str
    capability_status: CapabilityStatus
    succeeded: bool = False
    official: bool = False
    generated_document_id: str | None = None
    artifact_id: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeneratedDocument:
    generated_document_id: str
    request_id: str
    version: int
    output_format: TemplateFormat
    capability_status: CapabilityStatus
    artifact_id: str | None = None


@dataclass(frozen=True)
class FormatCapability:
    template_format: TemplateFormat
    capability_status: CapabilityStatus
    adapter_implemented: bool
    output_format_declared: bool


@dataclass(frozen=True)
class FormEngineCapabilities:
    contract_supported: bool
    official_generation_available: bool
    draft_preview_available: bool
    source_states_allowed_for_official_generation: tuple[str, ...]
    formats: tuple[FormatCapability, ...]

    def for_format(self, template_format: TemplateFormat) -> FormatCapability:
        for capability in self.formats:
            if capability.template_format is template_format:
                return capability
        raise ValueError(f"Unsupported template format: {template_format.value}")


PHASE_0_FORM_CAPABILITIES = FormEngineCapabilities(
    contract_supported=True,
    official_generation_available=False,
    draft_preview_available=False,
    source_states_allowed_for_official_generation=("APPROVED", "PUBLISHED"),
    formats=(
        FormatCapability(
            template_format=TemplateFormat.LEGACY_DOC,
            capability_status=CapabilityStatus.NOT_IMPLEMENTED,
            adapter_implemented=False,
            output_format_declared=True,
        ),
        FormatCapability(
            template_format=TemplateFormat.DOCX,
            capability_status=CapabilityStatus.DECLARED,
            adapter_implemented=False,
            output_format_declared=True,
        ),
        FormatCapability(
            template_format=TemplateFormat.PDF,
            capability_status=CapabilityStatus.DECLARED,
            adapter_implemented=False,
            output_format_declared=True,
        ),
    ),
)


def get_form_engine_capabilities() -> FormEngineCapabilities:
    return PHASE_0_FORM_CAPABILITIES


class SourceResolver(Protocol):
    def resolve(
        self,
        *,
        source: GenerationSource,
        source_id: str,
        source_version: int,
        source_path: str,
    ) -> object | None: ...


class Formatter(Protocol):
    def format(
        self,
        value: object,
        *,
        formatter_name: str,
        options: Mapping[str, object],
    ) -> str: ...


class TemplateAdapter(Protocol):
    template_format: TemplateFormat

    def capabilities(self) -> FormatCapability: ...

    def validate_template(self, definition: FormDefinition) -> tuple[str, ...]: ...

    def render(
        self,
        request: GenerationRequest,
        resolved_fields: Mapping[str, object],
    ) -> GenerationResult: ...

    def validate_result(self, result: GenerationResult) -> tuple[str, ...]: ...


# Concise aliases for callers that use the generic terms in the engine contract.
FormGenerationRequest = GenerationRequest
FormCatalogEntry = FormCatalog
Result = GenerationResult
SourceType = GenerationSource
