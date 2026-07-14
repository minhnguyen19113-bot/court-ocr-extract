from __future__ import annotations

import json
import time

import pytest

from court_ocr_extract.ocr_backends.surya_ocr import (
    SuryaRuntimeError,
    _RuntimeDiagnostics,
    _run_with_startup_timeout,
)


def test_runtime_diagnostics_records_last_stage(tmp_path) -> None:
    path = tmp_path / "surya_runtime_diagnostics.json"
    diagnostics = _RuntimeDiagnostics(path)

    diagnostics.stage("stage_06_create_predictor")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["last_stage"] == "stage_06_create_predictor"


def test_startup_timeout_fails_with_last_stage_and_diagnostics(tmp_path) -> None:
    path = tmp_path / "surya_runtime_diagnostics.json"
    diagnostics = _RuntimeDiagnostics(path)
    diagnostics.stage("stage_07_predictor_call")

    with pytest.raises(SuryaRuntimeError, match="stage_07_predictor_call"):
        _run_with_startup_timeout(
            lambda: time.sleep(0.2),
            timeout_seconds=0.02,
            diagnostics=diagnostics,
            docker_binary="synthetic-docker",
            check_container=False,
            container_spawn_check_seconds=1,
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "timeout"
    assert payload["last_stage"] == "stage_07_predictor_call"
    assert "possible_next_action" in payload

