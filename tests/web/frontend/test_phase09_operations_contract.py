from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.check_text_hygiene import validate_text


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_ROOT = ROOT / "scripts" / "web_demo"
WEB_DOCS = ROOT / "docs" / "web_demo"


def _source(name: str) -> str:
    return (SCRIPT_ROOT / name).read_text(encoding="utf-8")


def test_every_web_demo_powershell_script_parses() -> None:
    scripts = sorted(SCRIPT_ROOT.glob("*.ps1"))
    assert scripts
    for script in scripts:
        escaped_path = str(script).replace("'", "''")
        command = (
            f"$path = '{escaped_path}'; $errors = $null; "
            "[System.Management.Automation.Language.Parser]::ParseFile("
            "$path, [ref]$null, [ref]$errors) | Out-Null; "
            "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"{script.name}: {result.stderr}"


def test_launch_commands_keep_host_and_port_on_one_statement() -> None:
    backend = _source("run_backend.ps1")
    frontend = _source("run_frontend.ps1")
    assert (
        ".venv\\Scripts\\python.exe -m uvicorn court_ocr_extract.web_api.app:app "
        "--host 127.0.0.1 --port 8000"
    ) in backend
    assert "npm.cmd run dev -- --hostname 127.0.0.1 --port 3000" in frontend
    assert not any(line.strip() in {"--host", "--port"} for line in backend.splitlines())
    assert not any(line.strip() in {"--hostname", "--port"} for line in frontend.splitlines())


def test_prerequisite_helper_cannot_start_compose() -> None:
    source = _source("check_prerequisites.ps1").lower()
    assert "docker compose up" not in source
    assert "start-process" not in source


def test_scripts_exclude_unsafe_operator_commands() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in SCRIPT_ROOT.glob("*.ps1"))
    forbidden = (
        "0.0.0.0",
        "taskkill.exe /im",
        "git diff",
        "git clean",
        "git reset",
        "start-process http",
        "new-netfirewallrule",
        "netsh advfirewall",
    )
    assert not [token for token in forbidden if token in combined]


def test_start_launcher_is_static_and_owner_controlled() -> None:
    source = _source("start_local.ps1").lower()
    assert "run_backend.ps1" in source
    assert "run_frontend.ps1" in source
    assert "convertto-json" in source
    assert '@"' not in source
    assert "@'" not in source


def test_status_is_read_only_and_stop_uses_exact_state_pids() -> None:
    status = _source("status_local.ps1").lower()
    stop = _source("stop_local.ps1").lower()
    assert "stop-process" not in status
    assert "remove-item" not in status
    assert "docker compose -f $composepath ps" in status
    assert "invoke-restmethod" in status
    assert "get-ciminstance win32_process" in status
    assert "runtime-state.json" in stop
    assert "taskkill.exe /pid $processid" in stop
    assert "get-process -name" not in stop
    assert "taskkill.exe /im" not in stop


def test_phase09_known_issue_catalog_is_complete() -> None:
    source = (WEB_DOCS / "KNOWN_ISSUES_AND_RECOVERY.md").read_text(encoding="utf-8")
    codes = {
        "WEB-NODE-PATH-001",
        "WEB-NPM-LOCK-001",
        "WEB-ALEMBIC-IMPORT-001",
        "WEB-PS-LAUNCHER-001",
        "WEB-NEXT-SWC-LOCK-001",
        "WEB-DOCKER-STATE-001",
        "WEB-PORT-001",
        "WEB-AUDIT-001",
        "WEB-API-PROXY-001",
        "WEB-POWER-OFF-001",
    }
    labels = {
        "Ngày ghi nhận:",
        "Môi trường:",
        "Triệu chứng:",
        "Nguyên nhân gốc:",
        "Cách kiểm tra:",
        "Cách khắc phục:",
        "Phòng ngừa:",
        "Kết quả mong đợi:",
        "Log được phép:",
        "Dữ liệu cấm:",
        "Trạng thái:",
    }
    assert not {code for code in codes if f"## {code}" not in source}
    assert all(source.count(label) >= len(codes) for label in labels)


def test_local_run_guide_has_owner_boundary_and_all_launch_modes() -> None:
    source = (WEB_DOCS / "LOCAL_RUN_GUIDE.md").read_text(encoding="utf-8")
    assert "Chỉ Project Owner" in source
    assert "start_local.ps1 -InstallDependencies" in source
    assert "status_local.ps1" in source
    assert "stop_local.ps1" in source
    assert "-SkipDatabase" in source
    assert "-SkipMigration" in source
    assert "<REPO_ROOT>" in source


def test_git_performance_policy_is_persisted_in_required_memory() -> None:
    policy = "Không dùng git diff trong web worktree vì gây chậm/khựng trên máy Project Owner."
    required = (
        ROOT / "AGENTS.md",
        WEB_DOCS / "CODEX_OPERATING_RULES.md",
        WEB_DOCS / "DECISIONS.md",
        WEB_DOCS / "CODEX_WEB_HANDOFF.md",
    )
    assert all(policy in path.read_text(encoding="utf-8") for path in required)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("healthy\n", False),
        ("trailing  \n", True),
        ("missing newline", True),
        ("<<<" + "<<<< branch\n", True),
        ("C:/" + "Users/example/repo\n", True),
        ("-----BEGIN " + "PRIVATE KEY-----\n", True),
    ],
)
def test_text_hygiene_contract(tmp_path: Path, content: str, expected: bool) -> None:
    path = tmp_path / "fixture.md"
    path.write_text(content, encoding="utf-8", newline="")
    if content == "missing newline":
        path.write_bytes(content.encode("utf-8"))
    errors = validate_text(path)
    assert bool(errors) is expected
