from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

IMPORTANT_DOCS = [
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

KEY_MODULES = [
    "src/court_ocr_extract/ocr_cache.py",
    "src/court_ocr_extract/ocr/surya_adapter.py",
    "src/court_ocr_extract/ocr_backends/surya_ocr.py",
    "src/court_ocr_extract/vlm_page_reader.py",
    "src/court_ocr_extract/local_llm/json_parser.py",
    "src/court_ocr_extract/extraction/local_llm_extractor.py",
    "src/court_ocr_extract/extraction/validators.py",
    "src/court_ocr_extract/export/excel_writer.py",
    "src/court_ocr_extract/qa.py",
    "src/court_ocr_extract/visual_debug.py",
    "scripts/check_repo_guardrails.py",
    "scripts/check_architecture_guardrails.py",
    "scripts/repo_inventory.py",
    "scripts/import_graph.py",
]

MAIN_DECISIONS = [
    "Main candidate: Surya OCR + local LLM extraction.",
    "Benchmark path: local VLM end-to-end.",
    "Tesseract: legacy only, not main/default.",
    "PaddleOCR: not part of rebuild path.",
    "Cloud APIs: disabled by default and opt-in only.",
    "Synthetic smoke: contract/control-flow only.",
    "Canonical config: src/court_ocr_extract/settings.py.",
    "Canonical Excel writer: src/court_ocr_extract/excel_writer.py.",
]


def git_value(repo_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def build_snapshot(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    docs = {path: (repo_root / path).exists() for path in IMPORTANT_DOCS}
    modules = {path: (repo_root / path).exists() for path in KEY_MODULES}
    return {
        "repo_root": str(repo_root),
        "branch": git_value(repo_root, "branch", "--show-current"),
        "latest_commit": git_value(repo_root, "rev-parse", "--short", "HEAD"),
        "docs": docs,
        "modules": modules,
        "main_decisions": MAIN_DECISIONS,
        "protected_data_policy": "real data and real derived outputs are not inspected",
    }


def format_snapshot(snapshot: dict[str, Any]) -> str:
    docs = snapshot["docs"]
    modules = snapshot["modules"]
    lines = [
        "# Project Snapshot",
        f"repo_root: {snapshot['repo_root']}",
        f"branch: {snapshot['branch']}",
        f"latest_commit: {snapshot['latest_commit']}",
        f"protected_data_policy: {snapshot['protected_data_policy']}",
        "",
        "## Important Docs",
    ]
    for path, exists in docs.items():
        lines.append(f"- {'OK' if exists else 'MISSING'} {path}")
    lines.extend(["", "## Key Modules"])
    for path, exists in modules.items():
        lines.append(f"- {'OK' if exists else 'MISSING'} {path}")
    lines.extend(["", "## Main Decisions"])
    for decision in snapshot["main_decisions"]:
        lines.append(f"- {decision}")
    return "\n".join(lines)


def main() -> int:
    print(format_snapshot(build_snapshot()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
