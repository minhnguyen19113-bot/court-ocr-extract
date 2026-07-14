from __future__ import annotations

from types import SimpleNamespace

import pytest

from court_ocr_extract import cli
from court_ocr_extract.ocr_backends.base import OCRBackendStatus


def _args(**overrides):
    values = {
        "surya_docker_binary": r"C:\synthetic\docker.exe",
        "surya_runtime_check_gpu_container": False,
        "surya_runtime_timeout_seconds": 7,
        "skip_surya_runtime_preflight": False,
        "check_surya_runtime": False,
        "full_document": False,
        "pages": "1",
        "max_pages": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_preflight_uses_explicit_docker_binary(monkeypatch, tmp_path) -> None:
    captured = {}

    def collect(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "docker": {"binary": kwargs["docker_binary"], "error": None},
            "surya_api": {"kind": "synthetic"},
            "gpu_container": {"checked": False},
        }

    monkeypatch.setattr(cli, "collect_surya_runtime_diagnostics", collect)
    backend = SimpleNamespace(name="surya")

    cli._run_surya_runtime_preflight(_args(), backend, output_dir=tmp_path)

    assert captured["docker_binary"] == r"C:\synthetic\docker.exe"
    assert captured["runtime_timeout_seconds"] == 7
    assert (tmp_path / "surya_runtime_preflight.json").is_file()


def test_debug_review_preflight_runs_before_case_discovery(monkeypatch, tmp_path) -> None:
    events: list[str] = []
    backend = SimpleNamespace(
        name="surya",
        check_available=lambda: OCRBackendStatus("surya", True, "synthetic"),
    )
    monkeypatch.setattr(cli, "get_settings", lambda: SimpleNamespace(max_pages_before_marker=1, stop_marker=""))
    monkeypatch.setattr(cli, "get_ocr_backend", lambda *args: backend)
    monkeypatch.setattr(
        cli,
        "_run_surya_runtime_preflight",
        lambda *args, **kwargs: events.append("preflight"),
    )
    monkeypatch.setattr(cli, "_sample_case_files", lambda args: events.append("discover") or [])

    records = cli._run_sample_ocr(_args(ocr_backend="surya"), tmp_path)

    assert records == []
    assert events == ["preflight", "discover"]


def test_preflight_failure_prevents_predictor_path(monkeypatch, tmp_path) -> None:
    backend = SimpleNamespace(
        name="surya",
        check_available=lambda: OCRBackendStatus("surya", True, "synthetic"),
        ocr_pdf_prefix=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("predictor called")),
    )
    monkeypatch.setattr(cli, "get_settings", lambda: SimpleNamespace(max_pages_before_marker=1, stop_marker=""))
    monkeypatch.setattr(cli, "get_ocr_backend", lambda *args: backend)
    monkeypatch.setattr(
        cli,
        "_run_surya_runtime_preflight",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("synthetic preflight failure")),
    )
    monkeypatch.setattr(cli, "_sample_case_files", lambda args: (_ for _ in ()).throw(AssertionError("discovery called")))

    with pytest.raises(RuntimeError, match="synthetic preflight failure"):
        cli._run_sample_ocr(_args(ocr_backend="surya"), tmp_path)

