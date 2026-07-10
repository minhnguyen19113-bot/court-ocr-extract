from __future__ import annotations

from pathlib import Path

from scripts.check_repo_guardrails import (
    check_repository,
    classify_sensitive_paths,
    format_report,
)
from scripts.project_snapshot import build_snapshot


MEMORY_FILES = [
    "AGENTS.md",
    "docs/PROJECT_STATE.md",
    "docs/ARCHITECTURE.md",
    "docs/DECISIONS.md",
    "docs/TASKS.md",
    "docs/CHANGELOG_AI.md",
    "docs/CODEX_HANDOFF.md",
    "docs/PIPELINE_SPEC.md",
    "docs/DATA_SCHEMA.md",
    "docs/DEBUG_OUTPUT_SPEC.md",
    "docs/TESTING.md",
    "docs/MODEL_BENCHMARK.md",
    "docs/RUNBOOK_EZYCLOUDX.md",
    "docs/SECURITY_PRIVACY.md",
    "docs/CLEANUP_PLAN.md",
    "docs/AGENT_ROLES.md",
    "docs/REPO_INVENTORY.md",
    "docs/IMPORT_GRAPH.md",
    "docs/LEGACY_ARCHIVE_PLAN.md",
    "docs/PRODUCTION_TOOLKIT.md",
    "docs/EVALUATION_PLAN.md",
    "docs/GOLD_DATASET_GUIDE.md",
    "docs/PRIVACY_REDACTION_PLAN.md",
    "docs/OBSERVABILITY_PLAN.md",
    "docs/MLOPS_PLAN.md",
]


def create_memory_files(root: Path) -> None:
    for relative in MEMORY_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic\n", encoding="utf-8")


def test_classify_sensitive_paths_does_not_expose_names() -> None:
    counts = classify_sensitive_paths(
        [
            "data/raw_pdfs/private_case_name.pdf",
            "outputs/real_run/result.xlsx",
            ".env",
            "tests/fixtures/synthetic.png",
        ]
    )

    rendered = "\n".join(counts.keys())

    assert counts["protected:data/raw_pdfs"] == 1
    assert counts["protected:outputs"] == 1
    assert counts["env_file"] == 1
    assert "private_case_name" not in rendered


def test_guardrail_flags_tesseract_default_reference(tmp_path: Path) -> None:
    create_memory_files(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("python -m tool --ocr-backend tesseract\n", encoding="utf-8")

    report = check_repository(tmp_path, status_paths=[])

    assert not report.passed
    assert report.tesseract_default_findings[0].path == "README.md"


def test_guardrail_allows_tesseract_backend_file_without_default(tmp_path: Path) -> None:
    create_memory_files(tmp_path)
    backend = tmp_path / "src/court_ocr_extract/ocr_backends/tesseract_ocr.py"
    backend.parent.mkdir(parents=True, exist_ok=True)
    backend.write_text("class TesseractBackend: pass\n", encoding="utf-8")

    report = check_repository(tmp_path, status_paths=[], tracked_paths=[])

    assert report.passed


def test_guardrail_allows_tesseract_legacy_doc_reference(tmp_path: Path) -> None:
    create_memory_files(tmp_path)
    legacy_doc = tmp_path / "docs/legacy.md"
    legacy_doc.write_text("Tesseract is legacy optional only, not the main path.\n", encoding="utf-8")

    report = check_repository(tmp_path, status_paths=[], tracked_paths=[])

    assert report.passed


def test_guardrail_report_summarizes_sensitive_counts_without_paths(tmp_path: Path) -> None:
    create_memory_files(tmp_path)
    report = check_repository(
        tmp_path,
        status_paths=["data/private_pdfs/very_sensitive_name.pdf"],
        tracked_paths=[],
    )

    text = format_report(report)

    assert "protected:data/private_pdfs" in text
    assert "very_sensitive_name" not in text


def test_guardrail_flags_tracked_sensitive_path_without_printing_name(tmp_path: Path) -> None:
    create_memory_files(tmp_path)
    report = check_repository(
        tmp_path,
        status_paths=[],
        tracked_paths=["outputs/real_run/private_person.xlsx"],
    )

    text = format_report(report)

    assert not report.passed
    assert "protected:outputs" in text
    assert "private_person" not in text


def test_project_snapshot_reports_memory_doc_presence(tmp_path: Path) -> None:
    create_memory_files(tmp_path)

    snapshot = build_snapshot(tmp_path)

    assert snapshot["docs"]["AGENTS.md"] is True
    assert snapshot["docs"]["docs/PROJECT_STATE.md"] is True
