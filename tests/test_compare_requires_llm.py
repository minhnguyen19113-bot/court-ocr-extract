from __future__ import annotations

from argparse import Namespace

import pytest

from court_ocr_extract import cli
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult
from court_ocr_extract.ocr_cache import OCRCacheRecord
from court_ocr_extract.pre_content_ab import run_pre_content_ab_test
from court_ocr_extract.settings import PipelineSettings


def test_compare_require_llm_fails_before_case_processing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "read_ocr_cache_dir", lambda path: [_record()])
    monkeypatch.setattr(cli, "check_llm_backend", lambda settings: {
        "ok": False, "error_type": "llm_connection_failed", "error": "refused",
        "provider": "vllm", "model": "synthetic", "base_url": "http://127.0.0.1:8000/v1",
    })
    args = Namespace(
        ocr_cache_dir="synthetic", output_dir=str(tmp_path), strategies="llm_only", limit=1,
        require_llm=True, allow_llm_failure=False, skip_llm_preflight=False, open=False,
    )

    with pytest.raises(RuntimeError, match="preflight failed"):
        cli.cmd_compare_pre_content(args)
    assert not (tmp_path / "compare_summary.json").exists()


def test_unavailable_llm_has_no_fake_null_result_and_hybrid_keeps_rules(tmp_path) -> None:
    summary = run_pre_content_ab_test(
        [_record()], output_dir=tmp_path, settings=PipelineSettings(), llm_available=False,
        llm_preflight={"ok": False, "error_type": "llm_connection_failed", "error": "refused"},
        strategies=["hybrid_rule_llm", "llm_only"],
    )
    import json
    payload = json.loads((tmp_path / "cases" / "synthetic" / "llm_only_output.json").read_text(encoding="utf-8"))
    hybrid = json.loads((tmp_path / "cases" / "synthetic" / "hybrid_output.json").read_text(encoding="utf-8"))
    assert summary["case_count"] == 1
    assert payload["status"] == "llm_only_not_run"
    assert "metadata" not in payload
    assert hybrid["status"] == "hybrid_rule_only_fallback"
    assert hybrid["metadata"]["judgment_number"] == "01/2025/HS-ST"


def _record():
    texts = [
        "Bản án số: 01/2025/HS-ST",
        "NHÂN DANH",
        "Thẩm phán - Chủ tọa phiên tòa: Thẩm Phán Synthetic",
        "Đối với bị cáo:",
        "Người Synthetic A, sinh năm 1990",
        "Bị hại:",
        "Người Synthetic P",
        "NỘI DUNG VỤ ÁN",
    ]
    lines = [{"line_id": f"p001_l{i:04d}", "page_number": 1, "text": text} for i, text in enumerate(texts, 1)]
    return OCRCacheRecord("synthetic", 1, "synthetic", OCRResult(
        backend="synthetic", status="success", pages_processed=1, marker_found=True,
        marker_page=1, text="\n".join(texts), pages=[OCRPage(page_index=1, lines=lines)],
        metadata={"pages_total": 3, "early_stop": {"triggered": True}},
    ))
