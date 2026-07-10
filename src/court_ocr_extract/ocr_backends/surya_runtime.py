from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


WINDOWS_DOCKER_DESKTOP = Path(r"C:\Program Files\Docker\Docker\resources\bin\docker.exe")


def resolve_docker_binary() -> str | None:
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


def patch_surya_docker_resolver_if_needed() -> dict[str, Any]:
    binary = resolve_docker_binary()
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


def check_docker_cli(binary: str | None = None, *, include_info: bool = True) -> dict[str, Any]:
    binary = binary or resolve_docker_binary()
    if not binary:
        return {"available": False, "binary": None, "version": None, "info_ok": False, "error": "docker_binary_not_found"}
    version = _run([binary, "--version"])
    info = _run([binary, "info"]) if include_info else {"ok": None, "output": "", "error": None}
    return {
        "available": bool(version["ok"] and (info["ok"] is not False)),
        "binary": binary,
        "version": version["output"],
        "info_ok": info["ok"],
        "error": version["error"] or info["error"],
    }


def collect_surya_runtime_diagnostics(*, check_gpu_container: bool = False) -> dict[str, Any]:
    from court_ocr_extract.ocr_backends.surya_ocr import (
        SUPPORTED_SURYA_OCR_VERSION,
        installed_surya_ocr_version,
    )

    docker = check_docker_cli()
    diagnostics: dict[str, Any] = {
        "os": platform.platform(),
        "surya_ocr_version": installed_surya_ocr_version() or "not installed",
        "supported_surya_ocr_version": SUPPORTED_SURYA_OCR_VERSION,
        "docker": docker,
        "wsl": None,
        "gpu_container": {"checked": False},
    }
    if platform.system() == "Windows":
        wsl = shutil.which("wsl.exe") or shutil.which("wsl")
        diagnostics["wsl"] = _run([wsl, "--status"]) if wsl else {"ok": False, "error": "wsl_not_found", "output": ""}
    if check_gpu_container:
        binary = docker.get("binary")
        diagnostics["gpu_container"] = {
            "checked": True,
            **(_run([binary, "run", "--rm", "--gpus", "all", "nvidia/cuda:12.4.1-base-ubuntu22.04", "nvidia-smi"]) if binary else {"ok": False, "error": "docker_binary_not_found", "output": ""}),
        }
    return diagnostics


def _run(command: list[str | None], timeout: int = 20) -> dict[str, Any]:
    if not command[0]:
        return {"ok": False, "output": "", "error": "command_not_found"}
    try:
        completed = subprocess.run(
            [str(item) for item in command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "output": "", "error": f"{type(exc).__name__}: {exc}"}
    output = (completed.stdout or completed.stderr or "").strip()
    return {"ok": completed.returncode == 0, "output": output, "error": None if completed.returncode == 0 else output}
