from __future__ import annotations

from fastapi.testclient import TestClient

from court_ocr_extract.final_excel_schema import FINAL_EXCEL_COLUMNS
from court_ocr_extract.web_api.app import create_app


client = TestClient(create_app())


def test_system_endpoints_expose_phase_zero_contracts() -> None:
    health = client.get("/api/v1/system/health").json()
    assert health == {
        "status": "ok",
        "service": "court-ocr-web-api",
        "api_version": "v1",
        "environment": "local",
        "persistence": "foundation_only",
        "phase": "PHASE_0",
    }

    capabilities = client.get("/api/v1/system/capabilities").json()
    runtime_flags = {
        key: value
        for key, value in capabilities.items()
        if key.endswith("_runtime_available")
    }
    assert runtime_flags
    assert not any(runtime_flags.values())
    assert capabilities["ocr_backend"] == {
        "ownership": "external_core_integration",
        "runtime_available": False,
    }
    assert capabilities["mutation_endpoints_available"] is False
    assert capabilities["official_form_generation_source_states"] == [
        "APPROVED",
        "PUBLISHED",
    ]

    schema = client.get("/api/v1/system/schema").json()
    assert [column["key"] for column in schema["columns"]] == list(
        FINAL_EXCEL_COLUMNS
    )

    workflows = client.get("/api/v1/system/workflows").json()
    assert len(workflows["states"]) == 9
    assert len(workflows["field_statuses"]) == 8
    assert workflows["approved_is_published"] is False
    assert workflows["machine_output_can_publish"] is False


def test_schema_endpoint_fails_closed_for_future_domain() -> None:
    response = client.get(
        "/api/v1/system/schema",
        params={"case_domain": "civil"},
    )
    assert response.status_code == 404


def test_openapi_contains_only_safe_system_get_operations() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert set(paths) == {
        "/api/v1/system/health",
        "/api/v1/system/capabilities",
        "/api/v1/system/schema",
        "/api/v1/system/workflows",
        "/api/v1/forms/capabilities",
    }
    assert all(set(operations) == {"get"} for operations in paths.values())
