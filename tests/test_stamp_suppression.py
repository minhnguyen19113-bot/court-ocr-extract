from __future__ import annotations

import cv2
import numpy as np

from court_ocr_extract.image_processing.stamp_suppression import suppress_stamp_for_ocr


def _write(path, image) -> None:
    assert cv2.imwrite(str(path), image)


def test_balanced_suppression_creates_mask_and_reduces_synthetic_stamp(tmp_path) -> None:
    image = np.full((120, 160), 245, dtype=np.uint8)
    image[40:80, 60:100] = 30
    red = np.zeros_like(image)
    red[38:82, 58:102] = 255
    protection = np.zeros_like(image)
    _write(tmp_path / "image.png", image)
    _write(tmp_path / "red.png", red)
    _write(tmp_path / "protection.png", protection)

    metadata = suppress_stamp_for_ocr(
        tmp_path / "image.png", tmp_path / "red.png", tmp_path / "protection.png",
        tmp_path / "suppressed.png", tmp_path / "mask.png", mode="balanced"
    )

    output = cv2.imread(str(tmp_path / "suppressed.png"), cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(str(tmp_path / "mask.png"), cv2.IMREAD_GRAYSCALE)
    assert metadata["stamp_suppression_applied"] is True
    assert np.count_nonzero(mask) > 0
    assert float(output[50:70, 70:90].mean()) > float(image[50:70, 70:90].mean())


def test_missing_red_mask_is_a_valid_no_stamp_case(tmp_path) -> None:
    image = np.full((20, 20), 240, dtype=np.uint8)
    _write(tmp_path / "image.png", image)

    metadata = suppress_stamp_for_ocr(
        tmp_path / "image.png", tmp_path / "missing.png", tmp_path / "missing_protection.png",
        tmp_path / "suppressed.png", tmp_path / "mask.png", mode="balanced"
    )

    assert metadata["stamp_suppression_applied"] is False
    assert np.array_equal(cv2.imread(str(tmp_path / "suppressed.png"), 0), image)
