from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaseFile:
    case_id: str
    source_index: int
    path: Path
    pdf_hash: str | None = None


def discover_pdfs(input_dir: str | Path, *, limit: int | None = None) -> list[Path]:
    paths = sorted(Path(input_dir).glob("*.pdf"))
    if limit is not None:
        return paths[:limit]
    return paths


def case_file_for_path(path: str | Path, source_index: int, *, hash_bytes: bool = True) -> CaseFile:
    path = Path(path)
    digest = _hash_file(path) if hash_bytes else _hash_text(str(source_index))
    return CaseFile(
        case_id=f"case_{source_index:03d}_{digest[:8]}",
        source_index=source_index,
        path=path,
        pdf_hash=digest,
    )


def case_files_for_paths(paths: list[Path], *, hash_bytes: bool = True) -> list[CaseFile]:
    return [
        case_file_for_path(path, index, hash_bytes=hash_bytes)
        for index, path in enumerate(paths, start=1)
    ]


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
