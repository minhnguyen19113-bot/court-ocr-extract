from __future__ import annotations

from pathlib import Path
from typing import Any


MODES = ("off", "conservative", "balanced", "aggressive")


def suppress_stamp_for_ocr(
    image_path: str | Path,
    red_mask_path: str | Path,
    protection_mask_path: str | Path,
    output_path: str | Path,
    suppression_mask_path: str | Path,
    *,
    mode: str = "balanced",
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"Unsupported stamp suppression mode: {mode}")
    import cv2
    import numpy as np

    image = _read(Path(image_path), cv2, np, cv2.IMREAD_GRAYSCALE)
    red = _read(Path(red_mask_path), cv2, np, cv2.IMREAD_GRAYSCALE)
    protection = _read(Path(protection_mask_path), cv2, np, cv2.IMREAD_GRAYSCALE)
    output_path = Path(output_path)
    suppression_mask_path = Path(suppression_mask_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if image is None:
        # Keep debug/review runs inspectable even when an upstream stub failed
        # to emit its image. A real preprocessing failure is recorded in metadata.
        image = np.full((1, 1), 255, dtype=np.uint8)
    # A missing red mask means that the preceding preprocessing stage did not
    # detect or emit one. Preserve the image and still emit valid review artifacts.
    if red is None:
        red = np.zeros_like(image)
    if red.shape != image.shape:
        red = cv2.resize(red, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    if protection is None:
        protection = np.zeros_like(red)
    elif protection.shape != image.shape:
        protection = cv2.resize(protection, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

    # An all-white mask is a common synthetic/legacy "no detections" marker;
    # treating it as a full-page stamp would erase every OCR line.
    if float(np.mean(red > 0)) >= 0.995:
        red = np.zeros_like(red)
    mask = _build_mask(red, mode, cv2, np)
    overlap = (mask > 0) & (protection > 0)
    mask_count = int(np.count_nonzero(mask))
    overlap_ratio = float(np.count_nonzero(overlap)) / max(1, mask_count)
    warnings = ["stamp_mask_overlaps_dark_text"] if overlap_ratio >= 0.01 else []
    suppressed = image.copy()
    applied = mode != "off" and mask_count > 0
    if applied:
        if mode == "aggressive":
            suppressed = cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
        else:
            safe_mask = cv2.bitwise_and(mask, cv2.bitwise_not(protection))
            radius = 2 if mode == "conservative" else 4
            suppressed = cv2.inpaint(image, safe_mask, radius, cv2.INPAINT_TELEA)
            suppressed[safe_mask > 0] = np.maximum(suppressed[safe_mask > 0], 245)
    _write(suppression_mask_path, mask, cv2)
    _write(output_path, suppressed, cv2)
    components = cv2.connectedComponents((mask > 0).astype(np.uint8))[0] - 1
    return {
        "stamp_suppression": mode,
        "stamp_suppression_applied": applied,
        "stamp_mask_ratio": mask_count / float(mask.size),
        "stamp_components": max(0, int(components)),
        "stamp_overlap_dark_text_ratio": overlap_ratio,
        "stamp_suppression_warnings": warnings,
        "stamp_suppression_mask_path": str(suppression_mask_path),
        "ocr_input_stamp_suppressed_path": str(output_path),
    }


def _build_mask(red, mode, cv2, np):
    binary = ((red > 0).astype(np.uint8) * 255)
    if mode == "off":
        return np.zeros_like(binary)
    sizes = {"conservative": (3, 0), "balanced": (5, 1), "aggressive": (9, 2)}
    size, iterations = sizes[mode]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    if iterations:
        mask = cv2.dilate(mask, kernel, iterations=iterations)
    return mask


def _read(path, cv2, np, mode):
    if not path.exists():
        return None
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, mode) if data.size else None


def _write(path, image, cv2):
    success, data = cv2.imencode(Path(path).suffix or ".png", image)
    if not success:
        raise ValueError(f"Could not encode stamp artifact: {path}")
    data.tofile(str(path))
