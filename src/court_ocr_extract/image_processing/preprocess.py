from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from court_ocr_extract.image_processing.red_stamp_removal import reduce_red_stamp


def preprocess_for_ocr(
    rendered_image_path: str | Path,
    output_path: str | Path,
    *,
    remove_red_stamp: bool = False,
    intermediate_path: str | Path | None = None,
    red_stamp_mode: str = "mask_to_white",
) -> Path:
    """Create an OCR helper image in the required order.

    Required order:
    rendered PDF image -> helper image -> red stamp reduction -> preprocessing -> OCR.
    """
    rendered_image_path = Path(rendered_image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    working_path = rendered_image_path
    if remove_red_stamp:
        intermediate = Path(intermediate_path) if intermediate_path else output_path.with_name(
            output_path.stem + "_red_reduced" + output_path.suffix
        )
        reduce_red_stamp(rendered_image_path, intermediate, mode=red_stamp_mode)
        working_path = intermediate

    try:
        import cv2
        import numpy as np
    except Exception:
        _preprocess_with_pillow(working_path, output_path)
        return output_path

    image = _cv2_read_image(working_path, cv2, np)
    if image is None:
        shutil.copy2(working_path, output_path)
        return output_path

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = _deskew_gray(gray, cv2, np)
    gray = _balance_light(gray, cv2)
    gray = _enhance_contrast(gray, cv2)
    gray = cv2.fastNlMeansDenoising(gray, None, h=6, templateWindowSize=7, searchWindowSize=21)
    _cv2_write_image(output_path, gray, cv2)
    return output_path


def _preprocess_with_pillow(input_path: Path, output_path: Path) -> None:
    with Image.open(input_path) as image:
        processed = image.convert("L")
        processed = ImageOps.autocontrast(processed)
        processed = processed.filter(ImageFilter.SHARPEN)
        processed.save(output_path)


def _deskew_gray(gray, cv2, np):
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    threshold = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(threshold > 0))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.05 or abs(angle) > 15:
        return gray
    height, width = gray.shape[:2]
    rotation = cv2.getRotationMatrix2D((width // 2, height // 2), angle, 1.0)
    return cv2.warpAffine(
        gray,
        rotation,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def _balance_light(gray, cv2):
    background = cv2.medianBlur(gray, 31)
    balanced = cv2.divide(gray, background, scale=255)
    return balanced


def _enhance_contrast(gray, cv2):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _cv2_read_image(path: Path, cv2, np):
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _cv2_write_image(path: Path, image, cv2) -> None:
    success, data = cv2.imencode(path.suffix or ".png", image)
    if not success:
        raise ValueError(f"Could not encode processed image: {path}")
    data.tofile(str(path))
