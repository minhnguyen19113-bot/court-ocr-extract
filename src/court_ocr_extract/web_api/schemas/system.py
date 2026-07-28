from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str = "court-ocr-web-api"
    api_version: str = "v1"
    environment: str = "local"
    persistence: str = "foundation_only"
    phase: str = "PHASE_0"


class OcrBackendCapability(BaseModel):
    ownership: str = "external_core_integration"
    runtime_available: bool = False


class CapabilitiesResponse(BaseModel):
    api_version: str = "v1"
    environment: str = "local"
    phase: str = "PHASE_0"
    input_types_designed: tuple[str, ...] = ("pdf", "jpg", "jpeg", "png")
    export_types_designed: tuple[str, ...] = ("xlsx", "json", "html", "zip")
    document_generation_types_declared: tuple[str, ...] = ("doc", "docx", "pdf")
    active_case_domains: tuple[str, ...] = ("criminal",)
    future_case_domains: tuple[str, ...] = ("civil", "administrative")
    ocr_backend: OcrBackendCapability = OcrBackendCapability()
    supports_review_contract: bool = True
    supports_approval_contract: bool = True
    supports_publishing_contract: bool = True
    supports_form_generation_contract: bool = True
    mutation_endpoints_available: bool = False
    official_form_generation_source_states: tuple[str, ...] = (
        "APPROVED",
        "PUBLISHED",
    )
    pipeline_runtime_available: bool = False
    upload_runtime_available: bool = False
    publishing_runtime_available: bool = False
    form_generation_runtime_available: bool = False


class SchemaColumnResponse(BaseModel):
    key: str
    label: str
    export_order: int
    required: bool | None
    review_rule: str


class SchemaResponse(BaseModel):
    schema_id: str
    schema_version: str
    case_domain: str
    sheet_name: str
    columns: tuple[SchemaColumnResponse, ...]


class WorkflowTransitionResponse(BaseModel):
    source: str
    target: str


class WorkflowsResponse(BaseModel):
    workflow_id: str = "extraction-review-publishing"
    workflow_version: str = "1.0.0"
    case_domain: str = "criminal"
    states: tuple[str, ...]
    field_statuses: tuple[str, ...]
    transitions: tuple[WorkflowTransitionResponse, ...]
    approved_is_published: bool = False
    machine_output_can_publish: bool = False
