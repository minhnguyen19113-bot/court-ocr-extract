from __future__ import annotations

import json
import re
import shutil
import hashlib
from pathlib import Path
from typing import Any


SAFE_NAME_RE = re.compile(r"[^0-9A-Za-zÀ-ỹ._-]+", re.UNICODE)


def safe_stem(name: str) -> str:
    stem = Path(name).stem.strip()
    cleaned = SAFE_NAME_RE.sub("_", stem).strip("._")
    return cleaned or "document"


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        next_candidate = directory / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def store_original_pdf(pdf_path: Path, raw_pdf_dir: Path) -> Path:
    """Copy the source PDF into raw_pdfs without modifying the original file."""
    pdf_path = pdf_path.resolve()
    raw_pdf_dir.mkdir(parents=True, exist_ok=True)
    if raw_pdf_dir.resolve() in pdf_path.parents:
        return pdf_path
    target = unique_path(raw_pdf_dir, f"{safe_stem(pdf_path.name)}{pdf_path.suffix.lower()}")
    shutil.copy2(pdf_path, target)
    return target


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short_hash(value: str, length: int = 16) -> str:
    return value[:length]
