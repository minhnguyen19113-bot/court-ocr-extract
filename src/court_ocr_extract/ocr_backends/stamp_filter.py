from __future__ import annotations

from pathlib import Path
from typing import Any


THRESHOLDS = {
    "conservative": (0.75, 0.15),
    "balanced": (0.35, 0.50),
    "aggressive": (0.15, 1.01),
}


def filter_lines_by_stamp_mask(
    lines: list[dict[str, Any]],
    stamp_mask_path: str | Path | None,
    protection_mask_path: str | Path | None,
    *,
    mode: str = "balanced",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if mode == "off" or not stamp_mask_path or not Path(stamp_mask_path).exists():
        return [dict(line) for line in lines], []
    if mode not in THRESHOLDS:
        raise ValueError(f"Unsupported OCR stamp filter mode: {mode}")
    import cv2
    import numpy as np

    stamp = _read(Path(stamp_mask_path), cv2, np)
    protection = _read(Path(protection_mask_path), cv2, np) if protection_mask_path else None
    if stamp is None:
        return [dict(line) for line in lines], []
    if protection is None:
        protection = np.zeros_like(stamp)
    stamp_threshold, protection_keep = THRESHOLDS[mode]
    kept, excluded = [], []
    for line in lines:
        bbox = line.get("bbox")
        if not bbox:
            kept.append(dict(line))
            continue
        x1, y1, x2, y2 = _clip_bbox(bbox, stamp.shape[1], stamp.shape[0])
        area = max(1, (x2 - x1) * (y2 - y1))
        stamp_ratio = float(np.count_nonzero(stamp[y1:y2, x1:x2])) / area
        dark_ratio = float(np.count_nonzero(protection[y1:y2, x1:x2])) / area
        if stamp_ratio >= stamp_threshold and dark_ratio < protection_keep:
            item = dict(line)
            item.update(
                {
                    "reason": "stamp_mask_overlap",
                    "stamp_overlap_ratio": stamp_ratio,
                    "dark_text_overlap_ratio": dark_ratio,
                }
            )
            excluded.append(item)
        else:
            kept.append(dict(line))
    return kept, excluded


def _clip_bbox(bbox, width, height):
    x1, y1, x2, y2 = [int(round(float(value))) for value in bbox]
    return max(0, min(x1, width)), max(0, min(y1, height)), max(0, min(x2, width)), max(0, min(y2, height))


def _read(path, cv2, np):
    if not path.exists():
        return None
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_GRAYSCALE) if data.size else None
