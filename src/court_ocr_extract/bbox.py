from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def draw_bbox_overlay(
    image_path: str | Path,
    items: list[dict[str, Any]],
    output_path: str | Path,
    *,
    color: str = "red",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        for index, item in enumerate(items, start=1):
            bbox = item.get("bbox") or item.get("box")
            if not bbox or len(bbox) != 4:
                continue
            draw.rectangle([float(v) for v in bbox], outline=color, width=2)
            draw.text((float(bbox[0]), float(bbox[1])), f"{index:03d}", fill=color)
        image.save(output_path)
    return output_path


def backend_supports_bbox(pages: list[Any]) -> bool:
    for page in pages:
        if getattr(page, "words", None) or getattr(page, "lines", None) or getattr(page, "blocks", None):
            return True
    return False
