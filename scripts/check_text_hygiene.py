from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {
    ".git",
    ".next",
    ".npm-cache",
    ".venv",
    "__pycache__",
    "coverage",
    "node_modules",
}
PROTECTED_PREFIXES = (
    "data/raw_pdfs/",
    "data/private_pdfs/",
    "data/images/",
    "data/processed_images/",
    "data/ocr_raw/",
    "data/ocr_corrected/",
    "outputs/",
)
SECRET_MARKERS = (
    "-----BEGIN " + "PRIVATE KEY-----",
    "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
    "gh" + "p_",
    "github_" + "pat_",
    "sk-" + "proj-",
    "AK" + "IA",
)


def _git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def changed_text_paths() -> list[Path]:
    relative_paths = _git_paths("ls-files", "-m")
    relative_paths |= _git_paths("ls-files", "--others", "--exclude-standard")
    paths: list[Path] = []
    for relative in sorted(relative_paths):
        if relative.startswith(PROTECTED_PREFIXES):
            continue
        path = ROOT / relative
        if (
            path.is_file()
            and path.suffix.lower() in TEXT_SUFFIXES
            and not any(part in SKIP_PARTS for part in path.parts)
        ):
            paths.append(path)
    return paths


def validate_text(path: Path) -> list[str]:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        relative = path.name
    raw = path.read_bytes()
    errors: list[str] = []
    if b"\x00" in raw:
        return [f"{relative}: contains NUL byte"]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        return [f"{relative}: is not valid UTF-8 ({error})"]
    if raw and not raw.endswith(b"\n"):
        errors.append(f"{relative}: missing newline at end of file")
    for number, line in enumerate(text.splitlines(), start=1):
        if line.endswith((" ", "\t")):
            errors.append(f"{relative}:{number}: trailing whitespace")
    for marker in ("<<<" + "<<<< ", "===" + "====", ">>>" + ">>>> "):
        if marker in text:
            errors.append(f"{relative}: contains merge-conflict marker {marker.strip()}")
    lowered = text.lower()
    if "c:\\" + "users\\" in lowered or "c:/" + "users/" in lowered:
        errors.append(f"{relative}: contains a personal absolute Windows path")
    for marker in SECRET_MARKERS:
        if marker in text:
            errors.append(f"{relative}: contains possible secret marker {marker}")
    return errors


def main() -> int:
    paths = changed_text_paths()
    errors = [error for path in paths for error in validate_text(path)]
    if errors:
        print("Text hygiene failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Text hygiene passed for {len(paths)} changed text files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
