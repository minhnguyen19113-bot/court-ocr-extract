from __future__ import annotations

from pathlib import Path

from court_ocr_extract.config import PROJECT_ROOT


def load_prompt(path: str | Path | None, default_name: str) -> str:
    prompt_path = Path(path) if path else PROJECT_ROOT / "prompts" / default_name
    return prompt_path.read_text(encoding="utf-8")
