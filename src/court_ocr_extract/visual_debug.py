from __future__ import annotations

import html
import os
from datetime import datetime
from pathlib import Path


def make_run_dir(base_dir: str | Path, *, prefix: str = "run") -> Path:
    base_dir = Path(base_dir)
    run_id = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    path = base_dir / run_id
    counter = 2
    while path.exists():
        path = base_dir / f"{run_id}_{counter}"
        counter += 1
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_html(path: str | Path, title: str, body: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #111827; background: #f8fafc; }}
    main {{ max-width: 1180px; margin: 0 auto; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    section {{ margin: 0 0 24px; padding: 16px 0; border-top: 1px solid #d5dbe5; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    th, td {{ border: 1px solid #d5dbe5; padding: 8px; vertical-align: top; }}
    th {{ background: #e7f0f7; text-align: left; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #d5dbe5; background: #fff; }}
    pre {{ white-space: pre-wrap; background: #fff; border: 1px solid #d5dbe5; padding: 12px; max-height: 520px; overflow: auto; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .split {{ display: grid; grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr); gap: 18px; align-items: start; }}
    .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; background: #eef2ff; }}
    @media (max-width: 760px) {{ .split {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body><main>{body}</main></body>
</html>"""
    path.write_text(document, encoding="utf-8")
    return path


def escape(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def rel_link(target: Path, base: Path) -> str:
    target = target.resolve()
    base = base.resolve()
    try:
        return target.relative_to(base).as_posix()
    except ValueError:
        # Review artifacts may intentionally live in a sibling stage directory.
        return Path(os.path.relpath(target, base)).as_posix()
