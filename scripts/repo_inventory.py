from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "data",
    "dist",
    "logs",
    "models",
    "node_modules",
    "outputs",
    "venv",
    "work",
}

CODE_ROOTS = {"src", "scripts", "tests"}
DOC_ROOTS = {"docs", "prompts"}
CONFIG_ROOTS = {"config"}
ROOT_KEEP_FILES = {"AGENTS.md", "README.md", "pyproject.toml", ".env.example", ".gitignore"}

DUPLICATE_GROUPS = {
    "pdf_render": [
        "src/court_ocr_extract/pdf_render.py",
        "src/court_ocr_extract/pdf/render.py",
    ],
    "preprocess": [
        "src/court_ocr_extract/preprocess.py",
        "src/court_ocr_extract/image_preprocess.py",
        "src/court_ocr_extract/image_processing/preprocess.py",
    ],
    "surya_adapter": [
        "src/court_ocr_extract/ocr_backends/surya_ocr.py",
        "src/court_ocr_extract/ocr_surya.py",
        "src/court_ocr_extract/ocr/surya_adapter.py",
    ],
    "local_llm_extractor": [
        "src/court_ocr_extract/extraction/local_llm_extractor.py",
        "src/court_ocr_extract/extractors/local_llm_extractor.py",
    ],
    "validation": [
        "src/court_ocr_extract/validation.py",
        "src/court_ocr_extract/validator.py",
        "src/court_ocr_extract/extraction/validators.py",
    ],
}

LEGACY_PATHS = {
    "src/court_ocr_extract/ocr_backends/tesseract_ocr.py": "legacy optional OCR backend",
    "src/court_ocr_extract/ocr_backends/google_vision_ocr.py": "opt-in cloud OCR adapter",
    "src/court_ocr_extract/ocr_backends/google_document_ai_ocr.py": "opt-in cloud OCR adapter",
    "src/court_ocr_extract/ocr_backends/openai_vision_ocr.py": "opt-in cloud OCR adapter",
    "src/court_ocr_extract/ocr_backends/gemini_document_ocr.py": "opt-in cloud OCR adapter",
    "src/court_ocr_extract/extractors/openai_extractor.py": "opt-in cloud extractor",
    "src/court_ocr_extract/extractors/gemini_extractor.py": "opt-in cloud extractor",
    "src/court_ocr_extract/extraction/gliner_extractor.py": "experimental extractor",
}

OPTIONAL_APP_DIRS = ["app", "app_fastapi", "app_streamlit"]


@dataclass(frozen=True)
class RepoInventory:
    total_files: int
    by_top_folder: dict[str, int]
    by_extension: dict[str, int]
    code_files: int
    docs_files: int
    config_files: int
    root_files: int
    duplicate_groups: dict[str, list[str]]
    legacy_candidates: dict[str, str]
    optional_app_dirs: list[str]
    skipped_roots: list[str]

    @property
    def has_duplicate_groups(self) -> bool:
        return any(len(paths) > 1 for paths in self.duplicate_groups.values())


def iter_repo_files(repo_root: Path = REPO_ROOT) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        relative_parts = path.relative_to(repo_root).parts
        if any(part in SKIP_DIR_NAMES for part in relative_parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def _relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _top_folder(relative: str) -> str:
    if "/" not in relative:
        return "."
    return relative.split("/", 1)[0]


def _suffix(path: Path) -> str:
    return path.suffix.lower() or "[no extension]"


def _existing(paths: list[str], repo_root: Path) -> list[str]:
    return [path for path in paths if (repo_root / path).exists()]


def build_inventory(repo_root: Path = REPO_ROOT) -> RepoInventory:
    files = iter_repo_files(repo_root)
    relatives = [_relative(path, repo_root) for path in files]
    top_counts = Counter(_top_folder(path) for path in relatives)
    ext_counts = Counter(_suffix(path) for path in files)

    duplicate_groups = {
        name: existing
        for name, paths in DUPLICATE_GROUPS.items()
        if len(existing := _existing(paths, repo_root)) > 1
    }
    legacy_candidates = {
        path: reason for path, reason in LEGACY_PATHS.items() if (repo_root / path).exists()
    }
    optional_app_dirs = [path for path in OPTIONAL_APP_DIRS if (repo_root / path).exists()]

    return RepoInventory(
        total_files=len(files),
        by_top_folder=dict(sorted(top_counts.items())),
        by_extension=dict(sorted(ext_counts.items())),
        code_files=sum(1 for path in relatives if _top_folder(path) in CODE_ROOTS),
        docs_files=sum(1 for path in relatives if _top_folder(path) in DOC_ROOTS),
        config_files=sum(1 for path in relatives if _top_folder(path) in CONFIG_ROOTS),
        root_files=sum(1 for path in relatives if path in ROOT_KEEP_FILES),
        duplicate_groups=duplicate_groups,
        legacy_candidates=legacy_candidates,
        optional_app_dirs=optional_app_dirs,
        skipped_roots=sorted(SKIP_DIR_NAMES),
    )


def inventory_to_dict(inventory: RepoInventory) -> dict[str, Any]:
    return asdict(inventory)


def format_inventory(inventory: RepoInventory) -> str:
    lines = [
        "Repo inventory: PASS",
        f"Total safe files scanned: {inventory.total_files}",
        f"Code files: {inventory.code_files}",
        f"Docs/prompt files: {inventory.docs_files}",
        f"Config files: {inventory.config_files}",
        f"Root keep files: {inventory.root_files}",
        "",
        "Top folders:",
    ]
    for folder, count in inventory.by_top_folder.items():
        lines.append(f"- {folder}: {count}")

    lines.extend(["", "Duplicate/conflict groups:"])
    if inventory.duplicate_groups:
        for group, paths in inventory.duplicate_groups.items():
            lines.append(f"- {group}: {len(paths)} file(s)")
            for path in paths:
                lines.append(f"  - {path}")
    else:
        lines.append("- none detected")

    lines.extend(["", "Legacy/optional candidates:"])
    if inventory.legacy_candidates:
        for path, reason in inventory.legacy_candidates.items():
            lines.append(f"- {path}: {reason}")
    else:
        lines.append("- none detected")

    if inventory.optional_app_dirs:
        lines.extend(["", "Optional app dirs:"])
        for path in inventory.optional_app_dirs:
            lines.append(f"- {path}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a safe repo inventory without reading real data.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    inventory = build_inventory()
    if args.json:
        print(json.dumps(inventory_to_dict(inventory), ensure_ascii=False, indent=2))
    else:
        print(format_inventory(inventory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
