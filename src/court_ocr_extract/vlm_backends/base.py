from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class VLMBackendStatus:
    name: str
    available: bool
    reason: str = ""


@dataclass
class VLMPageResult:
    page_index: int
    text: str
    warnings: list[str] = field(default_factory=list)
    timing: dict[str, float] = field(default_factory=dict)
    raw_response: str | None = None
    unreadable_count: int = 0


class VLMBackend(Protocol):
    provider: str
    model_name: str

    def check_available(self) -> VLMBackendStatus:
        ...

    def read_page(self, image_path: Path, prompt: str, page_number: int) -> VLMPageResult:
        ...


def count_unreadable_markers(text: str) -> int:
    return (text or "").count("[KHONG DOC DUOC]") + (text or "").count("[KHÔNG ĐỌC ĐƯỢC]")

