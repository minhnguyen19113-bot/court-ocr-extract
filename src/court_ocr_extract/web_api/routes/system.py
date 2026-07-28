from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from court_ocr_extract.domain.field_status import FieldValueStatus
from court_ocr_extract.domain.schema_contract import (
    get_schema_contract,
)
from court_ocr_extract.domain.workflow import (
    WorkflowState,
    WorkflowTransitionValidator,
)
from court_ocr_extract.web_api.schemas.system import (
    CapabilitiesResponse,
    HealthResponse,
    SchemaColumnResponse,
    SchemaResponse,
    WorkflowTransitionResponse,
    WorkflowsResponse,
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/capabilities", response_model=CapabilitiesResponse)
def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse()


@router.get("/schema", response_model=SchemaResponse)
def schema(
    case_domain: str = Query(default="criminal"),
    schema_id: str = Query(default="criminal.final_excel"),
) -> SchemaResponse:
    try:
        contract = get_schema_contract(case_domain=case_domain, schema_id=schema_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SchemaResponse(
        schema_id=contract.schema_id,
        schema_version=contract.schema_version,
        case_domain=contract.case_domain,
        sheet_name=contract.sheet_name,
        columns=tuple(
            SchemaColumnResponse(
                key=column.key,
                label=column.label,
                export_order=column.export_order,
                required=column.required,
                review_rule=column.review_rule,
            )
            for column in contract.columns
        ),
    )


@router.get("/workflows", response_model=WorkflowsResponse)
def workflows() -> WorkflowsResponse:
    return WorkflowsResponse(
        states=tuple(state.value for state in WorkflowState),
        field_statuses=tuple(status.value for status in FieldValueStatus),
        transitions=tuple(
            WorkflowTransitionResponse(
                source=transition.source.value,
                target=transition.target.value,
            )
            for transition in WorkflowTransitionValidator.transitions()
        ),
    )
