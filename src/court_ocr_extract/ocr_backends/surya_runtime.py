from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


WINDOWS_DOCKER_DESKTOP = Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe")
DEFAULT_GPU_TEST_IMAGE = "nvidia/cuda:12.4.1-base-ubuntu22.04"
DEFAULT_GPU_CONTAINER_TIMEOUT_SECONDS = 180
OUTPUT_TAIL_CHARS = 4000


def resolve_docker_binary(explicit: str | None = None) -> str | None:
    if explicit and explicit.strip().strip('"'):
        return str(Path(explicit.strip().strip('"')))
    for name in ("SURYA_DOCKER_BINARY", "DOCKER_BINARY"):
        value = os.environ.get(name, "").strip().strip('"')
        if value:
            return str(Path(value))
    discovered = shutil.which("docker") or shutil.which("docker.exe")
    if discovered:
        return discovered
    if platform.system() == "Windows" and WINDOWS_DOCKER_DESKTOP.is_file():
        return str(WINDOWS_DOCKER_DESKTOP)
    return None


def patch_surya_docker_resolver_if_needed(binary: str | None = None) -> dict[str, Any]:
    binary = resolve_docker_binary(binary)
    if not binary:
        return {"patched": False, "docker_binary": None, "reason": "docker_binary_not_found"}
    try:
        module = importlib.import_module("surya.inference.backends.vllm")
    except (ImportError, ModuleNotFoundError):
        return {"patched": False, "docker_binary": binary, "reason": "surya_vllm_module_not_present"}
    resolver = getattr(module, "_resolve_docker_binary", None)
    if resolver is None:
        return {"patched": False, "docker_binary": binary, "reason": "surya_resolver_not_present"}
    module._resolve_docker_binary = lambda: binary
    return {"patched": True, "docker_binary": binary, "reason": "project_resolver_installed"}


def check_docker_cli(
    binary: str | None = None,
    *,
    include_info: bool = True,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    binary = resolve_docker_binary(binary)
    if not binary:
        return {
            "available": False,
            "binary": None,
            "version": None,
            "info_ok": False,
            "error": "docker_binary_not_found",
        }
    version = _run([binary, "--version"], timeout=timeout_seconds)
    info = (
        _run([binary, "info"], timeout=timeout_seconds)
        if include_info
        else {"ok": None, "stdout_tail": "", "stderr_tail": "", "error": None}
    )
    return {
        "available": bool(version["ok"] and (info["ok"] is not False)),
        "binary": binary,
        "version": version.get("stdout_tail") or version.get("stderr_tail"),
        "info_ok": info["ok"],
        "version_check": version,
        "info_check": info,
        "error": version.get("error") or info.get("error"),
    }


def collect_surya_runtime_diagnostics(
    *,
    check_gpu_container: bool = False,
    docker_binary: str | None = None,
    runtime_timeout_seconds: int = 20,
    gpu_container_timeout_seconds: int = DEFAULT_GPU_CONTAINER_TIMEOUT_SECONDS,
    gpu_test_image: str = DEFAULT_GPU_TEST_IMAGE,
) -> dict[str, Any]:
    from court_ocr_extract.ocr_backends.surya_ocr import (
        SUPPORTED_SURYA_OCR_VERSION,
        _detect_supported_surya_api,
        installed_surya_ocr_version,
        surya_version_guard_error,
    )

    binary = resolve_docker_binary(docker_binary)
    docker = check_docker_cli(binary, timeout_seconds=runtime_timeout_seconds)
    installed_version = installed_surya_ocr_version()
    version_error = surya_version_guard_error(installed_version)
    try:
        api = _detect_supported_surya_api()
        surya_api = {"ok": api.kind != "unsupported", "kind": api.kind, "details": api.details}
    except Exception as exc:
        surya_api = {"ok": False, "kind": "unavailable", "details": f"{type(exc).__name__}: {exc}"}
    diagnostics: dict[str, Any] = {
        "ok": bool(docker["available"] and not version_error and surya_api["ok"]),
        "os": platform.platform(),
        "surya_ocr_version": installed_version or "not installed",
        "supported_surya_ocr_version": SUPPORTED_SURYA_OCR_VERSION,
        "surya_version_ok": version_error is None,
        "surya_version_error": version_error,
        "surya_api": surya_api,
        "docker": docker,
        "wsl": None,
        "gpu_container": {"checked": False},
    }
    if platform.system() == "Windows":
        wsl = shutil.which("wsl.exe") or shutil.which("wsl")
        diagnostics["wsl"] = (
            _run([wsl, "--status"], timeout=runtime_timeout_seconds)
            if wsl
            else {"ok": False, "error": "wsl_not_found", "stdout_tail": "", "stderr_tail": ""}
        )
    if check_gpu_container:
        command = [
            binary,
            "run",
            "--rm",
            "--gpus",
            "all",
            gpu_test_image,
            "nvidia-smi",
        ]
        gpu_result = (
            _run(command, timeout=gpu_container_timeout_seconds)
            if binary
            else {
                "ok": False,
                "command": _command_text(command),
                "returncode": None,
                "stdout_tail": "",
                "stderr_tail": "",
                "error": "docker_binary_not_found",
            }
        )
        diagnostics["gpu_container"] = {"checked": True, **gpu_result}
        diagnostics["ok"] = bool(diagnostics["ok"] and gpu_result["ok"])
    return diagnostics


def check_running_surya_containers(binary: str | None, *, timeout_seconds: int = 15) -> dict[str, Any]:
    binary = resolve_docker_binary(binary)
    if not binary:
        return {"ok": False, "found": False, "error": "docker_binary_not_found"}
    result = _run(
        [binary, "ps", "--format", "{{.ID}}\t{{.Image}}\t{{.Names}}"],
        timeout=timeout_seconds,
    )
    output = result.get("stdout_tail", "")
    keywords = ("surya", "vllm")
    return {
        **result,
        "found": bool(result["ok"] and any(word in output.lower() for word in keywords)),
    }


def _run(command: list[str | None], timeout: int = 20) -> dict[str, Any]:
    command_text = _command_text(command)
    if not command or not command[0]:
        return {
            "ok": False,
            "command": command_text,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "error": "command_not_found",
        }
    normalized = [str(item) for item in command]
    try:
        completed = subprocess.run(
            normalized,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "command": command_text,
            "returncode": None,
            "stdout_tail": _tail(exc.stdout),
            "stderr_tail": _tail(exc.stderr),
            "error": "timeout",
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "ok": False,
            "command": command_text,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "error": f"{type(exc).__name__}: {exc}",
        }
    stdout_tail = _tail(completed.stdout)
    stderr_tail = _tail(completed.stderr)
    return {
        "ok": completed.returncode == 0,
        "command": command_text,
        "returncode": completed.returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "error": None if completed.returncode == 0 else (stderr_tail or stdout_tail or "command_failed"),
    }


def _tail(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    return (value or "").strip()[-OUTPUT_TAIL_CHARS:]


def _command_text(command: list[str | None]) -> str:
    return subprocess.list2cmdline([str(item) for item in command if item is not None])
