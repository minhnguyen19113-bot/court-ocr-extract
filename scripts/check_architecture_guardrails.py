from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

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

SAFE_TEXT_ROOTS = [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    ".env.example",
    "config",
    "docs",
    "scripts",
    "src",
    "tests",
]

MAIN_DEFAULT_ROOTS = [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    ".env.example",
    "config",
    "docs",
    "scripts",
    "src/court_ocr_extract/settings.py",
    "src/court_ocr_extract/config.py",
    "src/court_ocr_extract/cli.py",
]

PADDLE_MAIN_PATH_ROOTS = ["pyproject.toml", ".env.example", "config", "src"]
OLD_APP_DOC_ROOTS = ["README.md", "docs"]
OLD_APP_RUNTIME_ROOTS = ["scripts", "src"]
CANONICAL_EXCEL_WRITER = "src/court_ocr_extract/excel_writer.py"
LEGACY_EXCEL_WRITER_PATHS = [
    "src/court_ocr_extract/excel.py",
    "src/court_ocr_extract/export/excel_writer.py",
]
EXCEL_IMPORT_ROOTS = ["README.md", "docs", "scripts", "src", "tests"]

TESSERACT_DEFAULT_PATTERNS = [
    re.compile(r"\bocr_backend\s*[:=]\s*[\"']?tesseract\b", re.IGNORECASE),
    re.compile(r"\bOCR_BACKEND\s*=\s*tesseract\b", re.IGNORECASE),
    re.compile(r"_env\(\s*[\"']OCR_BACKEND[\"']\s*,\s*[\"']tesseract[\"']", re.IGNORECASE),
    re.compile(r"--ocr-backend\s+tesseract\b", re.IGNORECASE),
    re.compile(r"--backend\s+tesseract\b", re.IGNORECASE),
    re.compile(r"-OcrBackend\s+tesseract\b", re.IGNORECASE),
]

CLOUD_ENABLED_PATTERNS = [
    re.compile(r"\benable_cloud_ocr\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\benable_cloud_extraction\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\benable_cloud_llm_extraction\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bENABLE_CLOUD_OCR\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bENABLE_CLOUD_EXTRACTION\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bENABLE_CLOUD_LLM_EXTRACTION\s*=\s*true\b", re.IGNORECASE),
]

OLD_APP_DOC_MAIN_PATH_PATTERNS = [
    re.compile(r"\buvicorn\s+app(?:_fastapi)?\.main:app\b", re.IGNORECASE),
    re.compile(r"\bpython(?:\.exe)?\s+-m\s+uvicorn\s+app(?:_fastapi)?\.main:app\b", re.IGNORECASE),
    re.compile(r"\bstreamlit\s+run\s+app_streamlit[\\/]+main\.py\b", re.IGNORECASE),
]

OLD_APP_RUNTIME_PATTERNS = [
    re.compile(r"\bapp(?:_fastapi)?\.main:app\b", re.IGNORECASE),
    re.compile(r"\bapp_streamlit[\\/]+main\.py\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+app_fastapi\b", re.IGNORECASE),
    re.compile(r"\bimport\s+app_fastapi\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+app_streamlit\b", re.IGNORECASE),
    re.compile(r"\bimport\s+app_streamlit\b", re.IGNORECASE),
]

LEGACY_EXCEL_IMPORT_PATTERNS = [
    re.compile(
        r"\bfrom\s+court_ocr_extract\.(?:excel|export\.excel_writer)\s+import\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bimport\s+court_ocr_extract\.(?:excel|export\.excel_writer)\b",
        re.IGNORECASE,
    ),
]


@dataclass(frozen=True)
class ArchitectureGuardrailReport:
    failures: list[str]
    warnings: list[str]

    @property
    def passed(self) -> bool:
        return not self.failures


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


def is_protected_path(path: str) -> bool:
    normalized = normalize_repo_path(path)
    if is_allowed_synthetic_path(normalized):
        return False
    return normalized == ".env" or any(
        normalized.startswith(prefix) for prefix in PROTECTED_PREFIXES
    )


def git_paths(repo_root: Path, *args: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def iter_text_files(repo_root: Path, roots: list[str] | None = None) -> list[Path]:
    roots = SAFE_TEXT_ROOTS if roots is None else roots
    files: list[Path] = []
    suffixes = {".md", ".mmd", ".py", ".ps1", ".sh", ".toml", ".txt", ".yaml", ".yml", ".json"}
    for entry in roots:
        target = repo_root / entry
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            for child in target.rglob("*"):
                if child.is_file() and child.suffix.lower() in suffixes:
                    files.append(child)
    return sorted(set(files))


def count_pattern_matches(repo_root: Path, patterns: list[re.Pattern[str]], roots: list[str] | None = None) -> list[str]:
    findings: list[str] = []
    for path in iter_text_files(repo_root, roots):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        count = sum(len(pattern.findall(text)) for pattern in patterns)
        if count:
            findings.append(f"{relative}: {count}")
    return findings


def find_paddle_main_path_refs(repo_root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_text_files(repo_root, PADDLE_MAIN_PATH_ROOTS):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "paddleocr" in text or "paddle_ocr" in text:
            findings.append(relative)
    return findings


def find_old_app_main_path_refs(repo_root: Path) -> list[str]:
    findings = count_pattern_matches(repo_root, OLD_APP_DOC_MAIN_PATH_PATTERNS, OLD_APP_DOC_ROOTS)
    findings.extend(count_pattern_matches(repo_root, OLD_APP_RUNTIME_PATTERNS, OLD_APP_RUNTIME_ROOTS))
    return findings


def find_legacy_excel_import_refs(repo_root: Path) -> list[str]:
    return count_pattern_matches(
        repo_root,
        LEGACY_EXCEL_IMPORT_PATTERNS,
        EXCEL_IMPORT_ROOTS,
    )


def cli_has_bad_pages_default(repo_root: Path) -> bool:
    cli_path = repo_root / "src/court_ocr_extract/cli.py"
    if not cli_path.exists():
        return True
    text = cli_path.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"--pages[\s\S]{0,240}default\s*=\s*[\"']1-3[\"']", text))


def cli_has_full_document(repo_root: Path) -> bool:
    cli_path = repo_root / "src/court_ocr_extract/cli.py"
    if not cli_path.exists():
        return False
    return "--full-document" in cli_path.read_text(encoding="utf-8", errors="replace")


def surya_backend_has_forbidden_fallback(repo_root: Path) -> bool:
    surya_path = repo_root / "src/court_ocr_extract/ocr_backends/surya_ocr.py"
    if not surya_path.exists():
        return True
    text = surya_path.read_text(encoding="utf-8", errors="replace").lower()
    return any(token in text for token in ("tesseract", "paddleocr", "paddle_ocr"))


def check_architecture(repo_root: Path = REPO_ROOT) -> ArchitectureGuardrailReport:
    failures: list[str] = []
    warnings: list[str] = []

    tracked_protected = [path for path in git_paths(repo_root, "ls-files") if is_protected_path(path)]
    staged_protected = [
        path for path in git_paths(repo_root, "diff", "--cached", "--name-only") if is_protected_path(path)
    ]
    if tracked_protected:
        failures.append(f"Tracked protected real-data/output paths detected: {len(tracked_protected)}")
    if staged_protected:
        failures.append(f"Staged protected real-data/output paths detected: {len(staged_protected)}")

    tesseract_defaults = count_pattern_matches(repo_root, TESSERACT_DEFAULT_PATTERNS, MAIN_DEFAULT_ROOTS)
    if tesseract_defaults:
        failures.append("Tesseract default-like references: " + "; ".join(tesseract_defaults))

    cloud_defaults = count_pattern_matches(repo_root, CLOUD_ENABLED_PATTERNS, MAIN_DEFAULT_ROOTS)
    if cloud_defaults:
        failures.append("Cloud enabled-by-default references: " + "; ".join(cloud_defaults))

    paddle_refs = find_paddle_main_path_refs(repo_root)
    if paddle_refs:
        failures.append("PaddleOCR references in main safe paths: " + "; ".join(paddle_refs))

    old_app_refs = find_old_app_main_path_refs(repo_root)
    if old_app_refs:
        failures.append("Old app main-path references: " + "; ".join(old_app_refs))

    if not (repo_root / CANONICAL_EXCEL_WRITER).exists():
        failures.append(f"Canonical Excel writer is missing: {CANONICAL_EXCEL_WRITER}")
    legacy_excel_imports = find_legacy_excel_import_refs(repo_root)
    if legacy_excel_imports:
        failures.append(
            "Legacy Excel writer imports detected: " + "; ".join(legacy_excel_imports)
        )

    if cli_has_bad_pages_default(repo_root):
        failures.append("CLI still appears to default --pages to 1-3 or cli.py is missing.")
    if not cli_has_full_document(repo_root):
        failures.append("CLI is missing --full-document support.")
    if surya_backend_has_forbidden_fallback(repo_root):
        failures.append("Surya backend contains a forbidden fallback reference.")

    for folder in ("app", "app_fastapi", "app_streamlit"):
        if (repo_root / folder).exists():
            warnings.append(f"Legacy app folder still present: {folder}")
    for path in LEGACY_EXCEL_WRITER_PATHS:
        if (repo_root / path).exists():
            warnings.append(f"Legacy Excel compatibility path still present: {path}")
    duplicate_paths = [
        ("Surya adapters", ["src/court_ocr_extract/ocr_backends/surya_ocr.py", "src/court_ocr_extract/ocr_surya.py", "src/court_ocr_extract/ocr/surya_adapter.py"]),
        ("Validators", ["src/court_ocr_extract/validation.py", "src/court_ocr_extract/validator.py", "src/court_ocr_extract/extraction/validators.py"]),
    ]
    for label, paths in duplicate_paths:
        existing = [path for path in paths if (repo_root / path).exists()]
        if len(existing) > 1:
            warnings.append(f"Duplicate/conflict group needs cleanup decision: {label} ({len(existing)})")
    if (repo_root / "src/court_ocr_extract/ocr_backends/openai_vision_ocr.py").exists():
        warnings.append("Cloud OCR adapters exist but must remain opt-in.")
    if (repo_root / "src/court_ocr_extract/vlm_page_reader.py").exists():
        warnings.append("VLM benchmark path exists and must stay separate from main Surya path.")

    return ArchitectureGuardrailReport(failures=failures, warnings=warnings)


def format_report(report: ArchitectureGuardrailReport) -> str:
    lines = [f"Architecture guardrails: {'PASS' if report.passed else 'FAIL'}"]
    lines.extend(["", "Failures:"])
    if report.failures:
        lines.extend(f"- {failure}" for failure in report.failures)
    else:
        lines.append("- none")
    lines.extend(["", "Warnings:"])
    if report.warnings:
        lines.extend(f"- {warning}" for warning in report.warnings)
    else:
        lines.append("- none")
    return "\n".join(lines)


def main() -> int:
    report = check_architecture()
    print(format_report(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
