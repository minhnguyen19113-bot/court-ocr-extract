from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OcrEngineConfig:
    languages: list[str] = field(default_factory=lambda: ["vi"])
    use_mock: bool = False
