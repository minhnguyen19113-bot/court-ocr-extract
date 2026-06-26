from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_dir: Path, production: bool = False) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    level = logging.INFO if production else logging.DEBUG
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_dir / "processing.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)


def safe_text_for_log(text: str, allow_full_text: bool = False, max_chars: int = 240) -> str:
    if allow_full_text:
        return text
    text = " ".join((text or "").split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"
