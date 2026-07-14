from __future__ import annotations

from pathlib import Path

from court_ocr_extract.ocr_backends import surya_runtime


def test_env_override_wins_without_touching_docker(monkeypatch) -> None:
    monkeypatch.setenv("SURYA_DOCKER_BINARY", r"C:\synthetic\docker.exe")
    monkeypatch.setenv("DOCKER_BINARY", r"C:\other\docker.exe")
    monkeypatch.setattr(surya_runtime.shutil, "which", lambda name: None)

    assert surya_runtime.resolve_docker_binary() == r"C:\synthetic\docker.exe"


def test_windows_desktop_path_is_used_when_path_is_empty(monkeypatch) -> None:
    monkeypatch.delenv("SURYA_DOCKER_BINARY", raising=False)
    monkeypatch.delenv("DOCKER_BINARY", raising=False)
    monkeypatch.setattr(surya_runtime.shutil, "which", lambda name: None)
    monkeypatch.setattr(Path, "is_file", lambda self: str(self) == str(surya_runtime.WINDOWS_DOCKER_DESKTOP))

    assert surya_runtime.resolve_docker_binary() == str(surya_runtime.WINDOWS_DOCKER_DESKTOP)


def test_runtime_diagnostics_does_not_check_gpu_by_default(monkeypatch) -> None:
    calls: list[list[str | None]] = []

    monkeypatch.setattr(surya_runtime, "check_docker_cli", lambda *args, **kwargs: {
        "available": True, "binary": "docker", "version": "synthetic", "info_ok": True, "error": None
    })
    monkeypatch.setattr(surya_runtime, "_run", lambda command, timeout=20: calls.append(command) or {
        "ok": True, "output": "synthetic", "error": None
    })
    monkeypatch.setattr(surya_runtime, "platform", type("Platform", (), {
        "system": staticmethod(lambda: "Linux"),
        "platform": staticmethod(lambda: "synthetic"),
    }))
    monkeypatch.setattr(surya_runtime, "installed_surya_ocr_version", lambda: "0.20.0", raising=False)

    diagnostics = surya_runtime.collect_surya_runtime_diagnostics()

    assert diagnostics["gpu_container"] == {"checked": False}
    assert calls == []
