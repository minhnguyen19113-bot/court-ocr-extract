from __future__ import annotations

import subprocess
from types import SimpleNamespace

from court_ocr_extract.ocr_backends import surya_ocr, surya_runtime


def _patch_static_runtime(monkeypatch) -> None:
    monkeypatch.setattr(surya_runtime, "resolve_docker_binary", lambda explicit=None: explicit or "synthetic-docker")
    monkeypatch.setattr(
        surya_runtime,
        "check_docker_cli",
        lambda *args, **kwargs: {
            "available": True,
            "binary": args[0] if args else "synthetic-docker",
            "version": "synthetic",
            "info_ok": True,
            "error": None,
        },
    )
    monkeypatch.setattr(surya_runtime.platform, "system", lambda: "Linux")
    monkeypatch.setattr(surya_runtime.platform, "platform", lambda: "synthetic")
    monkeypatch.setattr(surya_ocr, "installed_surya_ocr_version", lambda: "0.20.0")
    monkeypatch.setattr(
        surya_ocr,
        "_detect_supported_surya_api",
        lambda: SimpleNamespace(kind="recognition_full_page", details="synthetic API"),
    )


def test_gpu_container_is_not_checked_without_flag(monkeypatch) -> None:
    _patch_static_runtime(monkeypatch)
    monkeypatch.setattr(surya_runtime, "_run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))

    diagnostics = surya_runtime.collect_surya_runtime_diagnostics(check_gpu_container=False)

    assert diagnostics["gpu_container"] == {"checked": False}


def test_gpu_container_success_sets_checked_true(monkeypatch) -> None:
    _patch_static_runtime(monkeypatch)
    monkeypatch.setattr(
        surya_runtime,
        "_run",
        lambda command, timeout=20: {
            "ok": True,
            "command": "synthetic-docker run",
            "returncode": 0,
            "stdout_tail": "synthetic nvidia-smi",
            "stderr_tail": "",
            "error": None,
        },
    )

    diagnostics = surya_runtime.collect_surya_runtime_diagnostics(check_gpu_container=True)

    assert diagnostics["gpu_container"]["checked"] is True
    assert diagnostics["gpu_container"]["ok"] is True
    assert diagnostics["gpu_container"]["returncode"] == 0


def test_gpu_container_failure_remains_checked(monkeypatch) -> None:
    _patch_static_runtime(monkeypatch)
    monkeypatch.setattr(
        surya_runtime,
        "_run",
        lambda command, timeout=20: {
            "ok": False,
            "command": "synthetic-docker run",
            "returncode": 125,
            "stdout_tail": "",
            "stderr_tail": "synthetic failure",
            "error": "synthetic failure",
        },
    )

    diagnostics = surya_runtime.collect_surya_runtime_diagnostics(check_gpu_container=True)

    assert diagnostics["gpu_container"]["checked"] is True
    assert diagnostics["gpu_container"]["ok"] is False


def test_run_timeout_has_explicit_timeout_error(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output="partial", stderr="waiting")

    monkeypatch.setattr(surya_runtime.subprocess, "run", timeout)

    result = surya_runtime._run(["synthetic-docker", "run"], timeout=1)

    assert result["ok"] is False
    assert result["error"] == "timeout"
    assert result["returncode"] is None
    assert result["stdout_tail"] == "partial"

