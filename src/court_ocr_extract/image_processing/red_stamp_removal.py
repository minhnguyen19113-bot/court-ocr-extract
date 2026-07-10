from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class RedStampResult:
    output_path: Path
    red_pixels_count: int
    red_pixels_ratio: float
    red_seal_removed: bool
    mask_path: Path | None = None
    warnings: list[str] = field(default_factory=list)


def reduce_red_stamp(
    input_path: str | Path,
    output_path: str | Path,
    mode: str = "mask_to_white",
    *,
    mask_path: str | Path | None = None,
) -> Path:
    """Reduce red pixels on a color OCR helper image without changing the source."""
    return reduce_red_stamp_with_metadata(
        input_path,
        output_path,
        mode=mode,
        mask_path=mask_path,
    ).output_path


def reduce_red_stamp_with_metadata(
    input_path: str | Path,
    output_path: str | Path,
    mode: str = "mask_to_white",
    *,
    mask_path: str | Path | None = None,
    max_red_ratio: float = 0.15,
) -> RedStampResult:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_mask_path = Path(mask_path) if mask_path else None
    if resolved_mask_path:
        resolved_mask_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cv2
        import numpy as np
    except Exception:
        return _fallback_reduce_red_with_pillow(
            input_path,
            output_path,
            mask_path=resolved_mask_path,
            max_red_ratio=max_red_ratio,
        )

    image = _cv2_read_image(input_path, cv2, np)
    if image is None:
        with Image.open(input_path) as source:
            source.convert("RGB").save(output_path)
        return RedStampResult(output_path, 0, 0.0, False, resolved_mask_path, ["red_seal_image_read_failed"])

    mask = _red_mask_hsv(image, cv2, np)
    red_pixels_count = int(np.count_nonzero(mask))
    red_pixels_ratio = red_pixels_count / float(mask.size) if mask.size else 0.0
    if resolved_mask_path:
        _cv2_write_image(resolved_mask_path, mask, cv2)

    warnings: list[str] = []
    if red_pixels_count == 0:
        warnings.append("red_seal_not_detected")
        reduced = image
        removed = False
    elif red_pixels_ratio > max_red_ratio:
        warnings.append("red_pixels_ratio_too_high")
        reduced = image
        removed = False
    else:
        if red_pixels_ratio < 0.00001:
            warnings.append("red_pixels_ratio_very_low")
        if mode == "inpaint":
            reduced = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
        else:
            reduced = image.copy()
            reduced[mask > 0] = (255, 255, 255)
        removed = True

    _cv2_write_image(output_path, reduced, cv2)
    return RedStampResult(
        output_path=output_path,
        red_pixels_count=red_pixels_count,
        red_pixels_ratio=red_pixels_ratio,
        red_seal_removed=removed,
        mask_path=resolved_mask_path,
        warnings=warnings,
    )


def _red_mask_hsv(image, cv2, np):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red_a = np.array([0, 80, 50])
    upper_red_a = np.array([10, 255, 255])
    lower_red_b = np.array([170, 80, 50])
    upper_red_b = np.array([180, 255, 255])
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower_red_a, upper_red_a),
        cv2.inRange(hsv, lower_red_b, upper_red_b),
    )
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.dilate(cleaned, kernel, iterations=1)


def _fallback_reduce_red_with_pillow(
    input_path: Path,
    output_path: Path,
    *,
    mask_path: Path | None,
    max_red_ratio: float,
) -> RedStampResult:
    with Image.open(input_path).convert("RGB") as source:
        image = source.copy()
    mask = Image.new("L", image.size, 0)
    pixels = image.load()
    mask_pixels = mask.load()
    red_pixels_count = 0
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]
            if r >= 120 and r > g * 1.35 and r > b * 1.35 and max(g, b) < 190:
                mask_pixels[x, y] = 255
                red_pixels_count += 1

    total = image.width * image.height
    red_pixels_ratio = red_pixels_count / float(total) if total else 0.0
    warnings: list[str] = ["red_seal_cv2_unavailable"]
    removed = 0 < red_pixels_ratio <= max_red_ratio
    if red_pixels_count == 0:
        warnings.append("red_seal_not_detected")
    elif red_pixels_ratio > max_red_ratio:
        warnings.append("red_pixels_ratio_too_high")
    if removed:
        for y in range(image.height):
            for x in range(image.width):
                if mask_pixels[x, y]:
                    pixels[x, y] = (255, 255, 255)
    if mask_path:
        mask.save(mask_path)
    image.save(output_path)
    return RedStampResult(output_path, red_pixels_count, red_pixels_ratio, removed, mask_path, warnings)


def _cv2_read_image(path: Path, cv2, np):
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _cv2_write_image(path: Path, image, cv2) -> None:
    success, data = cv2.imencode(path.suffix or ".png", image)
    if not success:
        raise ValueError(f"Could not encode image: {path}")
    data.tofile(str(path))
