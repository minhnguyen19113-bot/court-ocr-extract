from __future__ import annotations

from pathlib import Path

from court_ocr_extract.image_processing.preprocess import preprocess_for_ocr
from court_ocr_extract.image_processing.red_stamp_removal import reduce_red_stamp


def preprocess_image(
    image_path: str | Path,
    output_path: str | Path,
    remove_red_stamp: bool = False,
) -> Path:
    return preprocess_for_ocr(
        image_path,
        output_path,
        remove_red_stamp=remove_red_stamp,
    )


def preprocess_images(
    image_paths: list[Path],
    output_dir: str | Path,
    remove_red_stamp: bool = False,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed: list[Path] = []
    for image_path in image_paths:
        target = output_dir / image_path.name
        processed.append(preprocess_image(image_path, target, remove_red_stamp=remove_red_stamp))
    return processed


def reduce_red_stamp_hsv(image, cv2, np):
    """Lightly suppress red seals on OCR helper images using an HSV mask."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red_a = np.array([0, 60, 50])
    upper_red_a = np.array([12, 255, 255])
    lower_red_b = np.array([165, 60, 50])
    upper_red_b = np.array([180, 255, 255])
    mask_a = cv2.inRange(hsv, lower_red_a, upper_red_a)
    mask_b = cv2.inRange(hsv, lower_red_b, upper_red_b)
    mask = cv2.bitwise_or(mask_a, mask_b)
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    softened = image.copy()
    softened[mask > 0] = (255, 255, 255)
    return softened


def deskew_gray(gray, cv2, np):
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    threshold = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(threshold > 0))
    if coords.size == 0:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.05 or abs(angle) > 15:
        return gray

    height, width = gray.shape[:2]
    center = (width // 2, height // 2)
    rotation = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray,
        rotation,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def enhance_contrast(gray, cv2):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _cv2_read_image(path: Path, cv2, np):
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _cv2_write_image(path: Path, image, cv2) -> None:
    extension = path.suffix or ".png"
    success, data = cv2.imencode(extension, image)
    if not success:
        raise ValueError(f"Could not encode processed image: {path}")
    data.tofile(str(path))
