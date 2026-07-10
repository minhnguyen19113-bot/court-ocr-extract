from __future__ import annotations

from pathlib import Path

from scripts.check_architecture_guardrails import (
    check_architecture,
    cli_has_bad_pages_default,
    cli_has_full_document,
    find_legacy_excel_import_refs,
    find_old_app_main_path_refs,
    format_report,
    is_protected_path,
    surya_backend_has_forbidden_fallback,
)
from scripts.import_graph import build_import_graph
from scripts.repo_inventory import build_inventory


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repo_inventory_excludes_protected_real_data_roots() -> None:
    inventory = build_inventory(REPO_ROOT)

    assert inventory.total_files > 0
    assert "data" not in inventory.by_top_folder
    assert "outputs" not in inventory.by_top_folder
    assert "logs" not in inventory.by_top_folder
    assert "work" not in inventory.by_top_folder
    assert inventory.optional_app_dirs == []
    assert "surya_adapter" in inventory.duplicate_groups
    assert "excel_writer" not in inventory.duplicate_groups


def test_import_graph_scans_python_modules_and_reports_internal_edges() -> None:
    graph = build_import_graph(REPO_ROOT)

    assert "court_ocr_extract.cli" in graph.modules
    assert "scripts.project_snapshot" in graph.modules
    assert not graph.parse_errors
    assert any(module.startswith("court_ocr_extract.") for module in graph.reverse_imports)


def test_architecture_guardrails_pass_current_repo_without_real_data_scan() -> None:
    report = check_architecture(REPO_ROOT)
    rendered = format_report(report)

    assert report.passed, rendered
    assert "Architecture guardrails: PASS" in rendered


def test_architecture_guardrails_detect_protected_paths_without_printing_names() -> None:
    assert is_protected_path("data/raw_pdfs/private_name.pdf")
    assert is_protected_path("outputs/real_run/private_name.xlsx")
    assert not is_protected_path("outputs/debug_visual/synthetic_smoke/index.html")
    assert not is_protected_path("tests/fixtures/fake_ocr_text.txt")


def test_cli_full_document_guardrails_match_current_cli() -> None:
    assert not cli_has_bad_pages_default(REPO_ROOT)
    assert cli_has_full_document(REPO_ROOT)


def test_surya_backend_guardrail_has_no_forbidden_fallback() -> None:
    assert not surya_backend_has_forbidden_fallback(REPO_ROOT)


def test_architecture_guardrail_flags_old_app_run_instructions(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "old_ui.md").write_text(
        "Run old UI with: uvicorn app_fastapi.main:app --reload\n",
        encoding="utf-8",
    )

    findings = find_old_app_main_path_refs(tmp_path)

    assert findings == ["docs/old_ui.md: 1"]


def test_architecture_guardrail_flags_legacy_excel_imports(tmp_path: Path) -> None:
    source = tmp_path / "src/court_ocr_extract/pipeline.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from court_ocr_extract.export." + "excel_writer import write_excel\n",
        encoding="utf-8",
    )

    findings = find_legacy_excel_import_refs(tmp_path)

    assert findings == ["src/court_ocr_extract/pipeline.py: 1"]


def test_architecture_guardrail_requires_canonical_excel_writer(tmp_path: Path) -> None:
    report = check_architecture(tmp_path)

    assert any("Canonical Excel writer is missing" in failure for failure in report.failures)
