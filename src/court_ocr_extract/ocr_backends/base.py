from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class OCRBackendStatus:
    name: str
    available: bool
    reason: str = ""


@dataclass
class OCRPage:
    page_index: int
    text: str = ""
    blocks: list[dict[str, Any]] = field(default_factory=list)
    lines: list[dict[str, Any]] = field(default_factory=list)
    words: list[dict[str, Any]] = field(default_factory=list)
    image_path: str | None = None


@dataclass
class OCRResult:
    backend: str
    status: str
    pages_processed: int
    marker_found: bool
    marker_page: int | None
    text: str
    pages: list[OCRPage] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timing: dict[str, float] = field(default_factory=dict)
    cost_estimate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["pages"] = [asdict(page) for page in self.pages]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OCRResult":
        pages = [page if isinstance(page, OCRPage) else OCRPage(**page) for page in payload.get("pages", [])]
        return cls(
            backend=payload.get("backend", ""),
            status=payload.get("status", "failed"),
            pages_processed=int(payload.get("pages_processed", len(pages))),
            marker_found=bool(payload.get("marker_found", False)),
            marker_page=payload.get("marker_page"),
            text=payload.get("text", ""),
            pages=pages,
            warnings=list(payload.get("warnings", [])),
            timing=dict(payload.get("timing", {})),
            cost_estimate=payload.get("cost_estimate"),
        )


class OCRBackend(Protocol):
    name: str

    def check_available(self) -> OCRBackendStatus:
        ...

    def ocr_pdf_prefix(
        self,
        pdf_path: Path,
        max_pages: int,
        stop_marker: str,
        debug_visual: bool = False,
        work_dir: Path | None = None,
    ) -> OCRResult:
        ...
