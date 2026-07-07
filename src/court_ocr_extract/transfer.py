from __future__ import annotations

import zipfile
from pathlib import Path


def zip_debug_visual(run_id: str, *, debug_visual_dir: str | Path, output_path: str | Path) -> Path:
    debug_visual_dir = Path(debug_visual_dir)
    if run_id == "latest":
        candidates = sorted([path for path in debug_visual_dir.glob("run_*") if path.is_dir()])
        if not candidates:
            raise FileNotFoundError("No debug visual run directory found.")
        run_dir = candidates[-1]
    else:
        run_dir = debug_visual_dir / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(f"Debug visual run not found: {run_id}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in run_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(run_dir.parent))
    return output_path
