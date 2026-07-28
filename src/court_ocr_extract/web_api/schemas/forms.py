from __future__ import annotations

from pydantic import BaseModel

from court_ocr_extract.domain.form_engine import CapabilityStatus


class FormFormatCapabilityResponse(BaseModel):
    capability_status: CapabilityStatus
    adapter_implemented: bool
    output_format_declared: bool


class FormCapabilitiesResponse(BaseModel):
    contract_supported: bool
    official_generation_available: bool
    draft_preview_available: bool
    source_states_allowed_for_official_generation: tuple[str, ...]
    formats: dict[str, FormFormatCapabilityResponse]

