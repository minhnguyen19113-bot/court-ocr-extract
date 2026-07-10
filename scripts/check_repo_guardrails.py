from __future__ import annotations

import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

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

PROTECTED_PREFIXES = [
    "data/raw_pdfs/",
    "data/private_pdfs/",
    "data/images/",
    "data/processed_images/",
    "data/ocr_raw/",
    "data/ocr_corrected/",
    "outputs/",
    "logs/",
    "work/",
]

ALLOWED_SYNTHETIC_PREFIXES = [
    "outputs/debug_visual/synthetic_smoke/",
    "outputs/extraction_draft/synthetic_smoke/",
]

ALLOWED_SYNTHETIC_FILES = {
    "outputs/excel/synthetic_smoke.xlsx",
    "outputs/qa/synthetic_smoke_report.json",
}

SENSITIVE_EXTENSIONS = {
    ".pdf",
    ".xlsx",
    ".xls",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".sqlite",
    ".db",
}

SAFE_SCAN_ROOTS = [
    "README.md",
    "AGENTS.md",
    "docs",
    "config",
    "scripts",
    "src/court_ocr_extract/settings.py",
    "src/court_ocr_extract/config.py",
    ".env.example",
]

TESSERACT_DEFAULT_PATTERNS = [
    re.compile(r"\bocr_backend\s*[:=]\s*[\"']?tesseract\b", re.IGNORECASE),
    re.compile(r"\bocr_backend\s*:\s*\w+\s*=\s*[\"']tesseract[\"']", re.IGNORECASE),
    re.compile(r"\bOCR_BACKEND\s*=\s*tesseract\b", re.IGNORECASE),
    re.compile(r"\bOcrBackend\s*=\s*[\"']tesseract[\"']", re.IGNORECASE),
    re.compile(r"_env\(\s*[\"']OCR_BACKEND[\"']\s*,\s*[\"']tesseract[\"']", re.IGNORECASE),
    re.compile(r"--ocr-backend\s+tesseract\b", re.IGNORECASE),
    re.compile(r"--backend\s+tesseract\b", re.IGNORECASE),
    re.compile(r"-OcrBackend\s+tesseract\b", re.IGNORECASE),
]

CLOUD_DEFAULT_PATTERNS = [
    re.compile(r"\benable_cloud_ocr\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\benable_cloud_extraction\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\benable_cloud_llm_extraction\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bENABLE_CLOUD_OCR\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bENABLE_CLOUD_EXTRACTION\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bENABLE_CLOUD_LLM_EXTRACTION\s*=\s*true\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class TextFinding:
    path: str
    count: int


@dataclass(frozen=True)
class GuardrailReport:
    missing_memory_files: list[str]
    sensitive_worktree_counts: Counter[str]
    sensitive_tracked_counts: Counter[str]
    tesseract_default_findings: list[TextFinding]
    cloud_default_findings: list[TextFinding]

    @property
    def passed(self) -> bool:
        return not (
            self.missing_memory_files
            or self.sensitive_worktree_counts
            or self.sensitive_tracked_counts
            or self.tesseract_default_findings
            or self.cloud_default_findings
        )


def normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip().lower()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_allowed_synthetic_path(path: str) -> bool:
    normalized = normalize_repo_path(path)
    return normalized in ALLOWED_SYNTHETIC_FILES or any(
        normalized.startswith(prefix) for prefix in ALLOWED_SYNTHETIC_PREFIXES
    )


def classify_sensitive_paths(paths: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for raw_path in paths:
        normalized = normalize_repo_path(raw_path)
        if not normalized or is_allowed_synthetic_path(normalized):
            continue
        if normalized == ".env" or normalized.endswith("/.env"):
            counts["env_file"] += 1
            continue
        protected = next((prefix for prefix in PROTECTED_PREFIXES if normalized.startswith(prefix)), "")
        if protected:
            counts[f"protected:{protected.rstrip('/')}"] += 1
            continue
        suffix = Path(normalized).suffix
        if suffix in SENSITIVE_EXTENSIONS and not normalized.startswith("tests/fixtures/"):
            counts[f"sensitive_extension:{suffix}"] += 1
    return counts


def git_status_paths(repo_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--short"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path)
    return paths


def git_tracked_paths(repo_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def iter_safe_scan_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for entry in SAFE_SCAN_ROOTS:
        target = repo_root / entry
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            for child in target.rglob("*"):
                if child.is_file() and child.suffix.lower() in {
                    ".md",
                    ".mmd",
                    ".yaml",
                    ".yml",
                    ".json",
                    ".py",
                    ".ps1",
                    ".sh",
                    ".toml",
                    ".txt",
                }:
                    files.append(child)
    return sorted(set(files))


def count_pattern_findings(repo_root: Path, patterns: list[re.Pattern[str]]) -> list[TextFinding]:
    findings: list[TextFinding] = []
    for path in iter_safe_scan_files(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        if normalize_repo_path(relative) == ".env":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        count = sum(len(pattern.findall(text)) for pattern in patterns)
        if count:
            findings.append(TextFinding(relative, count))
    return findings


def check_repository(
    repo_root: Path = REPO_ROOT,
    status_paths: list[str] | None = None,
    tracked_paths: list[str] | None = None,
) -> GuardrailReport:
    missing_memory = [path for path in MEMORY_FILES if not (repo_root / path).exists()]
    worktree_paths = git_status_paths(repo_root) if status_paths is None else status_paths
    git_paths = git_tracked_paths(repo_root) if tracked_paths is None else tracked_paths
    return GuardrailReport(
        missing_memory_files=missing_memory,
        sensitive_worktree_counts=classify_sensitive_paths(worktree_paths),
        sensitive_tracked_counts=classify_sensitive_paths(git_paths),
        tesseract_default_findings=count_pattern_findings(repo_root, TESSERACT_DEFAULT_PATTERNS),
        cloud_default_findings=count_pattern_findings(repo_root, CLOUD_DEFAULT_PATTERNS),
    )


def format_report(report: GuardrailReport) -> str:
    lines = [f"Repo guardrails: {'PASS' if report.passed else 'FAIL'}"]
    lines.append("")
    lines.append("Memory files:")
    if report.missing_memory_files:
        for path in report.missing_memory_files:
            lines.append(f"- MISSING {path}")
    else:
        lines.append("- OK all required memory files exist")

    lines.append("")
    lines.append("Sensitive working tree paths:")
    if report.sensitive_worktree_counts:
        for category, count in sorted(report.sensitive_worktree_counts.items()):
            lines.append(f"- FAIL {category}: {count}")
    else:
        lines.append("- OK no sensitive working tree paths detected")

    lines.append("")
    lines.append("Sensitive tracked paths:")
    if report.sensitive_tracked_counts:
        for category, count in sorted(report.sensitive_tracked_counts.items()):
            lines.append(f"- FAIL {category}: {count}")
    else:
        lines.append("- OK no sensitive tracked paths detected")

    lines.append("")
    lines.append("Tesseract default references:")
    if report.tesseract_default_findings:
        for finding in report.tesseract_default_findings:
            lines.append(f"- FAIL {finding.path}: {finding.count} default-like reference(s)")
    else:
        lines.append("- OK no Tesseract default references detected")

    lines.append("")
    lines.append("Cloud defaults:")
    if report.cloud_default_findings:
        for finding in report.cloud_default_findings:
            lines.append(f"- FAIL {finding.path}: {finding.count} enabled-by-default reference(s)")
    else:
        lines.append("- OK cloud defaults remain disabled")
    return "\n".join(lines)


def main() -> int:
    report = check_repository()
    print(format_report(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
