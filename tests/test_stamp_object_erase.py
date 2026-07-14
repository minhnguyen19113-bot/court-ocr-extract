from __future__ import annotations

import cv2
import numpy as np

from court_ocr_extract.image_processing.stamp_suppression import suppress_stamp_for_ocr


def test_component_white_fill_covers_object_and_removes_gray_residual(tmp_path) -> None:
    image, red, protection = _stamp_page()
    _write_inputs(tmp_path, image, red, protection)
    mask_only = _run(tmp_path, "mask", prefix="mask")
    white_fill = _run(tmp_path, "component_white_fill", prefix="white")

    red_pixels = int(np.count_nonzero(red))
    object_mask = cv2.imread(str(tmp_path / "white_object_mask.png"), cv2.IMREAD_GRAYSCALE)
    mask_output = cv2.imread(str(tmp_path / "mask_output.png"), cv2.IMREAD_GRAYSCALE)
    white_output = cv2.imread(str(tmp_path / "white_output.png"), cv2.IMREAD_GRAYSCALE)

    assert white_fill["stamp_object_count"] == 1
    assert np.count_nonzero(object_mask) > red_pixels
    assert _residual(white_output) < _residual(mask_output) * 0.25
    assert mask_only["stamp_object_erased"] is False
    assert (tmp_path / "white_object_erased.png").exists()


def test_partial_red_mask_still_expands_over_low_saturation_stamp(tmp_path) -> None:
    image = np.full((180, 240), 250, dtype=np.uint8)
    image[55:130, 70:175] = 205
    red = np.zeros_like(image)
    cv2.rectangle(red, (85, 65), (160, 118), 255, 3)
    protection = np.zeros_like(image)
    _write_inputs(tmp_path, image, red, protection)

    metadata = _run(tmp_path, "component_white_fill", prefix="low_sat")
    object_mask = cv2.imread(str(tmp_path / "low_sat_object_mask.png"), cv2.IMREAD_GRAYSCALE)

    assert metadata["stamp_object_count"] == 1
    assert np.count_nonzero(object_mask[55:130, 70:175]) > np.count_nonzero(red[55:130, 70:175])


def test_dark_text_overlap_warns_and_preserves_black_text(tmp_path) -> None:
    image, red, protection = _stamp_page()
    image[82:98, 45:195] = 15
    protection[82:98, 45:195] = 255
    _write_inputs(tmp_path, image, red, protection)

    metadata = _run(tmp_path, "component_white_fill", prefix="overlap")
    output = cv2.imread(str(tmp_path / "overlap_output.png"), cv2.IMREAD_GRAYSCALE)

    assert metadata["stamp_object_dark_text_overlap_ratio"] >= 0.08
    assert "stamp_object_overlaps_dark_text" in metadata["stamp_object_warnings"]
    assert float(output[85:95, 80:160].mean()) < 80


def test_blank_page_and_small_red_noise_do_not_create_stamp_object(tmp_path) -> None:
    image = np.full((160, 220), 255, dtype=np.uint8)
    red = np.zeros_like(image)
    protection = np.zeros_like(image)
    _write_inputs(tmp_path, image, red, protection)
    blank = _run(tmp_path, "component_white_fill", prefix="blank")

    red[20:23, 20:23] = 255
    _write_inputs(tmp_path, image, red, protection)
    noise = _run(tmp_path, "component_white_fill", prefix="noise")

    assert blank["stamp_object_count"] == 0
    assert blank["stamp_object_erased"] is False
    assert noise["stamp_object_count"] == 0
    assert noise["stamp_object_mask_ratio"] == 0.0


def _stamp_page():
    image = np.full((180, 240), 250, dtype=np.uint8)
    image[55:130, 70:175] = 205
    red = np.zeros_like(image)
    cv2.rectangle(red, (70, 55), (175, 130), 255, 4)
    cv2.line(red, (85, 75), (160, 110), 255, 3)
    protection = np.zeros_like(image)
    return image, red, protection


def _write_inputs(tmp_path, image, red, protection):
    assert cv2.imwrite(str(tmp_path / "image.png"), image)
    assert cv2.imwrite(str(tmp_path / "red.png"), red)
    assert cv2.imwrite(str(tmp_path / "protection.png"), protection)


def _run(tmp_path, erase_mode, *, prefix):
    return suppress_stamp_for_ocr(
        tmp_path / "image.png",
        tmp_path / "red.png",
        tmp_path / "protection.png",
        tmp_path / f"{prefix}_output.png",
        tmp_path / f"{prefix}_suppression_mask.png",
        mode="balanced",
        erase_mode=erase_mode,
        stamp_object_mask_path=tmp_path / f"{prefix}_object_mask.png",
        stamp_object_erased_path=tmp_path / f"{prefix}_object_erased.png",
    )


def _residual(image):
    return int(np.count_nonzero(image[45:140, 60:185] < 235))
