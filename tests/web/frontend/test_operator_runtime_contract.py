from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WEB_DOCS = ROOT / "docs" / "web_demo"
HELPER = ROOT / "scripts" / "web_demo" / "check_prerequisites.ps1"


def test_required_phase06_operator_docs_exist() -> None:
    required = {
        WEB_DOCS / "CODEX_OPERATING_RULES.md",
        WEB_DOCS / "OPERATIONS_RUNBOOK.md",
        WEB_DOCS / "PORTS_AND_NETWORK.md",
        WEB_DOCS / "TROUBLESHOOTING.md",
    }
    assert not {path.relative_to(ROOT) for path in required if not path.is_file()}


def test_network_contract_defaults_to_loopback() -> None:
    compose = (
        ROOT / "ops" / "web_demo" / "docker-compose.postgres.yml"
    ).read_text(encoding="utf-8")
    network_doc = (WEB_DOCS / "PORTS_AND_NETWORK.md").read_text(encoding="utf-8")

    assert "127.0.0.1:${WEB_POSTGRES_PORT:-55432}:5432" in compose
    assert "127.0.0.1" in network_doc
    assert "NOT APPROVED IN PHASE 0.6" in network_doc


def test_troubleshooting_catalog_has_all_required_codes() -> None:
    source = (WEB_DOCS / "TROUBLESHOOTING.md").read_text(encoding="utf-8")
    codes = {
        "WEB-NODE-001",
        "WEB-NPM-001",
        "WEB-INSTALL-001",
        "WEB-LOCK-001",
        "WEB-TEST-001",
        "WEB-TSC-001",
        "WEB-LINT-001",
        "WEB-BUILD-001",
        "WEB-PORT-001",
        "WEB-PORT-002",
        "WEB-API-001",
        "WEB-CORS-001",
        "WEB-DB-001",
        "WEB-MIGRATION-001",
        "WEB-ENV-001",
        "WEB-NETWORK-001",
    }
    assert not {code for code in codes if code not in source}


def test_prerequisite_helper_is_read_only() -> None:
    source = HELPER.read_text(encoding="utf-8").lower()
    required = (
        "get-command",
        "--version",
        "npm.cmd",
        "package-lock.json",
        "getactivetcplisteners",
    )
    forbidden = (
        "start-process",
        "stop-process",
        "docker compose up",
        "docker run",
        "uvicorn",
        "npm run dev",
        "next dev",
        "netsh",
        "new-netfirewallrule",
        "remove-item",
    )

    assert all(token in source for token in required)
    assert not [token for token in forbidden if token in source]
