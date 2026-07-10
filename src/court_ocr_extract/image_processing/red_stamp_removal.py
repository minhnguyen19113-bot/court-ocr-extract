from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image


RED_REMOVAL_MODES = ("neutralize", "inpaint", "white_fill")


@dataclass(frozen=True)
class RedStampResult:
    output_path: Path
    red_pixels_count: int
    red_pixels_ratio: float
    red_seal_removed: bool
    mask_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    red_mask_components: int = 0
    red_mask_method: str = "hsv+lab+rgb"
    red_removal_mode: str = "neutralize"
    red_removed_ratio: float = 0.0
    red_residual_ratio_estimate: float = 0.0
    dark_text_overlap_ratio: float = 0.0
    black_text_protection_path: Path | None = None


def reduce_red_stamp(
    input_path: str | Path,
    output_path: str | Path,
    mode: str = "neutralize",
    *,
    mask_path: str | Path | None = None,
    black_text_protection_path: str | Path | None = None,
) -> Path:
    """Reduce red pixels on a color OCR helper image without changing the source."""
    return reduce_red_stamp_with_metadata(
        input_path,
        output_path,
        mode=mode,
        mask_path=mask_path,
        black_text_protection_path=black_text_protection_path,
    ).output_path


def reduce_red_stamp_with_metadata(
    input_path: str | Path,
    output_path: str | Path,
    mode: str = "neutralize",
    *,
    mask_path: str | Path | None = None,
    black_text_protection_path: str | Path | None = None,
    max_red_ratio: float = 0.15,
) -> RedStampResult:
    mode = _normalize_mode(mode)
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_mask_path = Path(mask_path) if mask_path else None
    protection_path = Path(black_text_protection_path) if black_text_protection_path else None
    for artifact_path in (resolved_mask_path, protection_path):
        if artifact_path:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cv2
        import numpy as np
    except Exception:
        return _fallback_reduce_red_with_pillow(
            input_path,
            output_path,
            mode=mode,
            mask_path=resolved_mask_path,
            protection_path=protection_path,
            max_red_ratio=max_red_ratio,
        )

    image = _cv2_read_image(input_path, cv2, np)
    if image is None:
        with Image.open(input_path) as source:
            source.convert("RGB").save(output_path)
        return RedStampResult(
            output_path,
            0,
            0.0,
            False,
            resolved_mask_path,
            ["red_seal_image_read_failed"],
            red_removal_mode=mode,
            black_text_protection_path=protection_path,
        )

    mask, components = _combined_red_mask(image, cv2, np)
    protection = _black_text_protection_mask(image, cv2, np)
    red_pixels_count = int(np.count_nonzero(mask))
    red_pixels_ratio = red_pixels_count / float(mask.size) if mask.size else 0.0
    overlap_count = int(np.count_nonzero((mask > 0) & (protection > 0)))
    overlap_ratio = overlap_count / float(max(1, red_pixels_count))
    if resolved_mask_path:
        _cv2_write_image(resolved_mask_path, mask, cv2)
    if protection_path:
        _cv2_write_image(protection_path, protection, cv2)

    warnings: list[str] = []
    if overlap_ratio >= 0.01:
        warnings.append("red_mask_overlaps_dark_text")
    if red_pixels_count == 0:
        warnings.append("red_seal_not_detected")
        reduced = image
        removed = False
    elif red_pixels_ratio > max_red_ratio:
        warnings.append("red_pixels_ratio_too_high")
        reduced = image
        removed = False
    else:
        safe_mask = cv2.bitwise_and(mask, cv2.bitwise_not(protection))
        reduced = _apply_red_removal(image, safe_mask, mode, cv2, np)
        removed = bool(np.count_nonzero(safe_mask))

    residual_mask = _raw_red_signal(reduced, cv2, np)
    residual_count = int(np.count_nonzero(residual_mask))
    residual_ratio = residual_count / float(residual_mask.size) if residual_mask.size else 0.0
    removed_ratio = max(0.0, (red_pixels_count - residual_count) / float(max(1, red_pixels_count)))
    _cv2_write_image(output_path, reduced, cv2)
    return RedStampResult(
        output_path=output_path,
        red_pixels_count=red_pixels_count,
        red_pixels_ratio=red_pixels_ratio,
        red_seal_removed=removed,
        mask_path=resolved_mask_path,
        warnings=warnings,
        red_mask_components=components,
        red_mask_method="hsv+lab+rgb",
        red_removal_mode=mode,
        red_removed_ratio=removed_ratio,
        red_residual_ratio_estimate=residual_ratio,
        dark_text_overlap_ratio=overlap_ratio,
        black_text_protection_path=protection_path,
    )


def _normalize_mode(mode: str) -> str:
    aliases = {"mask_to_white": "white_fill"}
    normalized = aliases.get(mode, mode)
    if normalized not in RED_REMOVAL_MODES:
        raise ValueError(f"Unsupported red removal mode: {mode}")
    return normalized


def _combined_red_mask(image, cv2, np):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv_mask = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 55, 45]), np.array([10, 255, 255])),
        cv2.inRange(hsv, np.array([170, 55, 45]), np.array([180, 255, 255])),
    )

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lab_red = cv2.inRange(lab[:, :, 1], 145, 255)
    blue, green, red = cv2.split(image)
    rgb_red = (
        (red.astype(np.int16) >= green.astype(np.int16) + 24)
        & (red.astype(np.int16) >= blue.astype(np.int16) + 24)
        & (red >= 95)
    ).astype(np.uint8) * 255
    lab_rgb = cv2.bitwise_and(lab_red, rgb_red)
    combined = cv2.bitwise_or(hsv_mask, lab_rgb)

    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, open_kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, close_kernel)
    cleaned = cv2.dilate(cleaned, open_kernel, iterations=1)
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    components = sum(1 for index in range(1, component_count) if stats[index, cv2.CC_STAT_AREA] >= 4)
    return cleaned, components


def _raw_red_signal(image, cv2, np):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv_mask = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 45, 35]), np.array([12, 255, 255])),
        cv2.inRange(hsv, np.array([168, 45, 35]), np.array([180, 255, 255])),
    )
    blue, green, red = cv2.split(image)
    rgb_mask = (
        (red.astype(np.int16) >= green.astype(np.int16) + 18)
        & (red.astype(np.int16) >= blue.astype(np.int16) + 18)
        & (red >= 80)
    ).astype(np.uint8) * 255
    return cv2.bitwise_or(hsv_mask, rgb_mask)


def _black_text_protection_mask(image, cv2, np):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    channel_range = image.max(axis=2).astype(np.int16) - image.min(axis=2).astype(np.int16)
    neutral_dark = ((gray < 145) & (channel_range < 48)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    return cv2.dilate(neutral_dark, kernel, iterations=1)


def _apply_red_removal(image, safe_mask, mode: str, cv2, np):
    if not np.count_nonzero(safe_mask):
        return image.copy()
    if mode == "inpaint":
        reduced = cv2.inpaint(image, safe_mask, 4, cv2.INPAINT_TELEA)
        residual = _raw_red_signal(reduced, cv2, np)
        local_region = cv2.dilate(safe_mask, np.ones((3, 3), np.uint8), iterations=1)
        residual = cv2.bitwise_and(residual, local_region)
        if np.count_nonzero(residual):
            reduced = cv2.inpaint(reduced, residual, 3, cv2.INPAINT_TELEA)
        return reduced
    reduced = image.copy()
    if mode == "white_fill":
        reduced[safe_mask > 0] = (255, 255, 255)
        return reduced

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kernel_size = max(15, (min(image.shape[:2]) // 20) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    local_neutral = cv2.merge([background, background, background])
    reduced[safe_mask > 0] = local_neutral[safe_mask > 0]
    return reduced


def _fallback_reduce_red_with_pillow(
    input_path: Path,
    output_path: Path,
    *,
    mode: str,
    mask_path: Path | None,
    protection_path: Path | None,
    max_red_ratio: float,
) -> RedStampResult:
    with Image.open(input_path).convert("RGB") as source:
        image = source.copy()
    mask = Image.new("L", image.size, 0)
    protection = Image.new("L", image.size, 0)
    pixels = image.load()
    mask_pixels = mask.load()
    protection_pixels = protection.load()
    red_pixels_count = overlap_count = 0
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]
            is_red = r >= 100 and r >= g + 24 and r >= b + 24
            is_dark_text = max(r, g, b) < 145 and max(r, g, b) - min(r, g, b) < 48
            if is_red:
                mask_pixels[x, y] = 255
                red_pixels_count += 1
            if is_dark_text:
                protection_pixels[x, y] = 255
            if is_red and is_dark_text:
                overlap_count += 1

    total = max(1, image.width * image.height)
    red_pixels_ratio = red_pixels_count / total
    overlap_ratio = overlap_count / max(1, red_pixels_count)
    warnings = ["red_seal_cv2_unavailable"]
    if overlap_ratio >= 0.01:
        warnings.append("red_mask_overlaps_dark_text")
    removed = 0 < red_pixels_ratio <= max_red_ratio
    if red_pixels_count == 0:
        warnings.append("red_seal_not_detected")
    elif red_pixels_ratio > max_red_ratio:
        warnings.append("red_pixels_ratio_too_high")
    if removed:
        for y in range(image.height):
            for x in range(image.width):
                if mask_pixels[x, y] and not protection_pixels[x, y]:
                    pixels[x, y] = (255, 255, 255)
    if mask_path:
        mask.save(mask_path)
    if protection_path:
        protection.save(protection_path)
    image.save(output_path)
    residual = sum(
        1
        for r, g, b in image.getdata()
        if r >= 100 and r >= g + 24 and r >= b + 24
    )
    return RedStampResult(
        output_path=output_path,
        red_pixels_count=red_pixels_count,
        red_pixels_ratio=red_pixels_ratio,
        red_seal_removed=removed,
        mask_path=mask_path,
        warnings=warnings,
        red_mask_components=0,
        red_mask_method="rgb_pillow_fallback",
        red_removal_mode=mode,
        red_removed_ratio=max(0.0, (red_pixels_count - residual) / max(1, red_pixels_count)),
        red_residual_ratio_estimate=residual / total,
        dark_text_overlap_ratio=overlap_ratio,
        black_text_protection_path=protection_path,
    )


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
