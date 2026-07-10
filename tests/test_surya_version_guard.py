from __future__ import annotations

import sys

import pytest

import court_ocr_extract.ocr_backends.surya_ocr as surya_module
from court_ocr_extract.ocr_backends.base import OCRBackendStatus
from court_ocr_extract.ocr_backends.surya_ocr import (
    SUPPORTED_SURYA_OCR_VERSION,
    SuryaAPIDetection,
    SuryaOCRBackend,
    surya_version_guard_error,
)
from court_ocr_extract.settings import PipelineSettings


def test_version_0200_passes_guard_and_adapter_check(monkeypatch) -> None:
    monkeypatch.setattr(surya_module, "installed_surya_ocr_version", lambda: "0.20.0")
    monkeypatch.setattr(
        surya_module,
        "_detect_supported_surya_api",
        lambda: SuryaAPIDetection("recognition_full_page", "0.20.0", "synthetic"),
    )
    monkeypatch.setattr(surya_module.importlib, "import_module", lambda name: object())

    status = SuryaOCRBackend(PipelineSettings()).check_available()

    assert surya_version_guard_error("0.20.0") is None
    assert status.available is True
    assert "Version: 0.20.0" in status.reason
    assert f"Supported version: {SUPPORTED_SURYA_OCR_VERSION}" in status.reason


def test_version_0211_fails_before_surya_import_or_runtime(monkeypatch) -> None:
    monkeypatch.setattr(surya_module, "installed_surya_ocr_version", lambda: "0.21.1")
    monkeypatch.setattr(
        surya_module.importlib,
        "import_module",
        lambda name: (_ for _ in ()).throw(AssertionError("Surya/Docker runtime must not be imported")),
    )

    status = SuryaOCRBackend(PipelineSettings()).check_available()

    assert status.available is False
    assert "currently supports surya-ocr==0.20.0" in status.reason
    assert "Detected surya-ocr 0.21.1" in status.reason
    assert "Surya 2 inference backend / Docker" in status.reason
    assert "pip uninstall -y surya-ocr" in status.reason
    assert "pip install -e" in status.reason


def test_missing_distribution_fails_before_import(monkeypatch) -> None:
    monkeypatch.setattr(surya_module, "installed_surya_ocr_version", lambda: "")
    monkeypatch.setattr(
        surya_module.importlib,
        "import_module",
        lambda name: (_ for _ in ()).throw(AssertionError("missing package must fail before import")),
    )

    status = SuryaOCRBackend(PipelineSettings()).check_available()

    assert status.available is False
    assert "surya-ocr is not installed" in status.reason
    assert "surya-ocr==0.20.0" in status.reason


def test_check_ocr_backend_only_calls_availability_check(monkeypatch, capsys) -> None:
    from scripts import check_ocr_backend

    backend = _AvailabilityOnlyBackend()
    monkeypatch.setattr(check_ocr_backend, "get_ocr_backend", lambda name: backend)
    monkeypatch.setattr(check_ocr_backend, "installed_surya_ocr_version", lambda: "0.20.0")
    monkeypatch.setattr(sys, "argv", ["check_ocr_backend", "--backend", "surya"])

    check_ocr_backend.main()

    output = capsys.readouterr().out
    assert "Installed version: 0.20.0" in output
    assert "Supported version: 0.20.0" in output
    assert "Available: True" in output
    assert backend.inference_called is False


def test_wrong_version_status_causes_check_script_failure(monkeypatch, capsys) -> None:
    from scripts import check_ocr_backend

    backend = _UnavailableBackend()
    monkeypatch.setattr(check_ocr_backend, "get_ocr_backend", lambda name: backend)
    monkeypatch.setattr(check_ocr_backend, "installed_surya_ocr_version", lambda: "0.21.1")
    monkeypatch.setattr(sys, "argv", ["check_ocr_backend", "--backend", "surya"])

    with pytest.raises(SystemExit) as exc_info:
        check_ocr_backend.main()

    assert exc_info.value.code == 1
    assert "Installed version: 0.21.1" in capsys.readouterr().out


class _AvailabilityOnlyBackend:
    name = "surya"
    inference_called = False

    def check_available(self):
        return OCRBackendStatus("surya", True, "synthetic version guard")

    def ocr_pdf_prefix(self, *args, **kwargs):
        self.inference_called = True
        raise AssertionError("check script must not call inference")


class _UnavailableBackend(_AvailabilityOnlyBackend):
    def check_available(self):
        return OCRBackendStatus("surya", False, "synthetic unsupported version")
