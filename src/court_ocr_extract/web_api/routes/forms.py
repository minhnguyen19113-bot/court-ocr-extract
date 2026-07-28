from __future__ import annotations

from fastapi import APIRouter

from court_ocr_extract.services.form_service import FormService
from court_ocr_extract.web_api.schemas.forms import (
    FormCapabilitiesResponse,
    FormFormatCapabilityResponse,
)


router = APIRouter(prefix="/forms", tags=["forms"])


@router.get("/capabilities", response_model=FormCapabilitiesResponse)
def capabilities() -> FormCapabilitiesResponse:
    capabilities = FormService().capabilities()
    return FormCapabilitiesResponse(
        contract_supported=capabilities.contract_supported,
        official_generation_available=capabilities.official_generation_available,
        draft_preview_available=capabilities.draft_preview_available,
        source_states_allowed_for_official_generation=(
            capabilities.source_states_allowed_for_official_generation
        ),
        formats={
            capability.template_format.value: FormFormatCapabilityResponse(
                capability_status=capability.capability_status,
                adapter_implemented=capability.adapter_implemented,
                output_format_declared=capability.output_format_declared,
            )
            for capability in capabilities.formats
        },
    )

