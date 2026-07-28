from __future__ import annotations

from fastapi.testclient import TestClient

from court_ocr_extract.web_api.app import create_app


client = TestClient(create_app())


def test_form_capabilities_match_phase_zero_contract() -> None:
    response = client.get("/api/v1/forms/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "contract_supported": True,
        "official_generation_available": False,
        "draft_preview_available": False,
        "source_states_allowed_for_official_generation": [
            "APPROVED",
            "PUBLISHED",
        ],
        "formats": {
            "legacy_doc": {
                "capability_status": "NOT_IMPLEMENTED",
                "adapter_implemented": False,
                "output_format_declared": True,
            },
            "docx": {
                "capability_status": "DECLARED",
                "adapter_implemented": False,
                "output_format_declared": True,
            },
            "pdf": {
                "capability_status": "DECLARED",
                "adapter_implemented": False,
                "output_format_declared": True,
            },
        },
    }


def test_app_exposes_exactly_five_read_only_phase_zero_operations() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert set(paths) == {
        "/api/v1/system/health",
        "/api/v1/system/capabilities",
        "/api/v1/system/schema",
        "/api/v1/system/workflows",
        "/api/v1/forms/capabilities",
    }
    assert all(set(operations) == {"get"} for operations in paths.values())

