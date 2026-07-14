from __future__ import annotations

import cv2
import numpy as np

from court_ocr_extract.image_processing.stamp_suppression import suppress_stamp_for_ocr


def test_disconnected_horizontal_stamp_is_grouped_from_union_seed(tmp_path) -> None:
    image, red, protection = _page_with_horizontal_stamp(include_side_seal=False)
    metadata = _run(tmp_path, image, red, protection, prefix="horizontal")
    object_seed = cv2.imread(str(tmp_path / "horizontal_seed.png"), cv2.IMREAD_GRAYSCALE)
    object_mask = cv2.imread(str(tmp_path / "horizontal_object.png"), cv2.IMREAD_GRAYSCALE)

    assert np.count_nonzero(object_seed) >= np.count_nonzero(red)
    assert metadata["stamp_object_count"] >= 1
    assert float(np.mean(object_mask[65:120, 25:220] > 0)) > 0.70
    assert metadata["object_seed_mask_path"].endswith("horizontal_seed.png")


def test_side_seal_does_not_displace_main_horizontal_stamp(tmp_path) -> None:
    image, red, protection = _page_with_horizontal_stamp(include_side_seal=True)
    metadata = _run(tmp_path, image, red, protection, prefix="both")
    object_mask = cv2.imread(str(tmp_path / "both_object.png"), cv2.IMREAD_GRAYSCALE)

    horizontal_coverage = float(np.mean(object_mask[65:120, 25:220] > 0))
    side_coverage = float(np.mean(object_mask[55:140, 275:350] > 0))
    assert horizontal_coverage > 0.70
    assert side_coverage > 0.30
    assert metadata["stamp_object_count"] >= 2


def _page_with_horizontal_stamp(*, include_side_seal):
    image = np.full((220, 360), 250, dtype=np.uint8)
    image[72:112, 35:210] = 210
    red = np.zeros_like(image)
    for x in range(38, 205, 20):
        cv2.rectangle(red, (x, 78), (x + 8, 105), 255, -1)
    if include_side_seal:
        cv2.circle(red, (315, 95), 31, 255, 4)
        image[62:128, 282:348] = 215
    protection = np.zeros_like(image)
    return image, red, protection


def _run(tmp_path, image, red, protection, *, prefix):
    for name, value in (("image", image), ("red", red), ("protection", protection)):
        assert cv2.imwrite(str(tmp_path / f"{name}.png"), value)
    return suppress_stamp_for_ocr(
        tmp_path / "image.png", tmp_path / "red.png", tmp_path / "protection.png",
        tmp_path / f"{prefix}_output.png", tmp_path / f"{prefix}_suppression.png",
        mode="balanced", erase_mode="component_white_fill",
        object_seed_mask_path=tmp_path / f"{prefix}_seed.png",
        stamp_object_mask_path=tmp_path / f"{prefix}_object.png",
        stamp_object_erased_path=tmp_path / f"{prefix}_erased.png",
    )
