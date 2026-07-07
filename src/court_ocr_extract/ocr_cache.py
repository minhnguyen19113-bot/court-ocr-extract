from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from court_ocr_extract.ocr_backends.base import OCRResult


@dataclass
class OCRCacheRecord:
    case_id: str
    source_index: int
    pdf_hash: str | None
    result: OCRResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "source_index": self.source_index,
            "pdf_hash": self.pdf_hash,
            "result": self.result.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OCRCacheRecord":
        return cls(
            case_id=payload["case_id"],
            source_index=int(payload.get("source_index", 0)),
            pdf_hash=payload.get("pdf_hash"),
            result=OCRResult.from_dict(payload["result"]),
        )


def write_ocr_cache_record(record: OCRCacheRecord, cache_dir: str | Path) -> Path:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{record.case_id}.json"
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_ocr_cache_record(path: str | Path) -> OCRCacheRecord:
    return OCRCacheRecord.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def read_ocr_cache_dir(cache_dir: str | Path) -> list[OCRCacheRecord]:
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return []
    return [read_ocr_cache_record(path) for path in sorted(cache_dir.glob("case_*.json"))]


def safe_cache_metadata(record: OCRCacheRecord) -> dict[str, Any]:
    return {
        "case_id": record.case_id,
        "source_index": record.source_index,
        "pdf_hash": record.pdf_hash,
        "backend": record.result.backend,
        "pages_processed": record.result.pages_processed,
        "marker_found": record.result.marker_found,
        "marker_page": record.result.marker_page,
        "status": record.result.status,
        "warnings": list(record.result.warnings),
        "timing": dict(record.result.timing),
    }
