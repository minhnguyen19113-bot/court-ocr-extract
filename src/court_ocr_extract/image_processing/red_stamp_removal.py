from __future__ import annotations

from pathlib import Path

from PIL import Image


def reduce_red_stamp(
    input_path: str | Path,
    output_path: str | Path,
    mode: str = "mask_to_white",
) -> Path:
    """Reduce red seals on an OCR helper image only.

    This function never modifies the original rendered page.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cv2
        import numpy as np
    except Exception:
        _fallback_reduce_red_with_pillow(input_path, output_path)
        return output_path

    image = _cv2_read_image(input_path, cv2, np)
    if image is None:
        Image.open(input_path).save(output_path)
        return output_path

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red_a = np.array([0, 55, 45])
    upper_red_a = np.array([12, 255, 255])
    lower_red_b = np.array([165, 55, 45])
    upper_red_b = np.array([180, 255, 255])
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower_red_a, upper_red_a),
        cv2.inRange(hsv, lower_red_b, upper_red_b),
    )
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    if mode == "inpaint":
        reduced = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
    else:
        reduced = image.copy()
        reduced[mask > 0] = (255, 255, 255)

    _cv2_write_image(output_path, reduced, cv2)
    return output_path


def _fallback_reduce_red_with_pillow(input_path: Path, output_path: Path) -> None:
    with Image.open(input_path).convert("RGB") as image:
        pixels = image.load()
        width, height = image.size
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if r > 120 and r > g * 1.25 and r > b * 1.25:
                    pixels[x, y] = (255, 255, 255)
        image.save(output_path)


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
