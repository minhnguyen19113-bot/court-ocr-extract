from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageStat


def assess_image_quality(image_path: str | Path) -> dict[str, float | bool]:
    image_path = Path(image_path)
    with Image.open(image_path).convert("L") as image:
        stat = ImageStat.Stat(image)
        contrast = float(stat.stddev[0])
        width, height = image.size
    too_small = width < 900 or height < 1200
    too_low_contrast = contrast < 18
    return {
        "width": float(width),
        "height": float(height),
        "contrast_std": contrast,
        "too_small": too_small,
        "too_low_contrast": too_low_contrast,
        "needs_review": bool(too_small or too_low_contrast),
    }
