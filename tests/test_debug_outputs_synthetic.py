from __future__ import annotations

import json

from scripts.smoke_synthetic_debug import run_smoke


def test_synthetic_smoke_creates_manual_review_outputs(tmp_path):
    result = run_smoke(
        output_root=tmp_path / "outputs",
        synthetic_root=tmp_path / "contract_fixtures",
    )

    manifest_path = tmp_path / "outputs" / "debug_visual" / "synthetic_smoke" / "manifest.json"
    debug_index = tmp_path / "outputs" / "debug_visual" / "synthetic_smoke" / "index.html"
    preview_index = tmp_path / "outputs" / "debug_visual" / "synthetic_smoke" / "extraction_preview" / "index.html"
    excel_path = tmp_path / "outputs" / "excel" / "synthetic_smoke.xlsx"
    qa_report = tmp_path / "outputs" / "qa" / "synthetic_smoke_report.json"
    draft_jsonl = tmp_path / "outputs" / "extraction_draft" / "synthetic_smoke" / "draft_internal.jsonl"

    assert result["manifest_path"] == str(manifest_path)
    assert manifest_path.exists()
    assert debug_index.exists()
    assert preview_index.exists()
    assert excel_path.exists()
    assert qa_report.exists()
    assert draft_jsonl.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["real_data_accessed"] is False
    assert all(step["pass"] for step in manifest["steps"])
    assert "data/raw_pdfs" not in json.dumps(manifest)
    assert "data\\raw_pdfs" not in json.dumps(manifest)
