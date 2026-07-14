from __future__ import annotations

import cv2
import numpy as np

from court_ocr_extract.image_processing.stamp_suppression import suppress_stamp_for_ocr


def test_selects_stamp_object_erased_when_it_is_cleaner_and_preserves_text(tmp_path) -> None:
    image, red, protection = _candidate_page()
    metadata = _run(tmp_path, image, red, protection)
    final = cv2.imread(str(tmp_path / "final.png"), cv2.IMREAD_GRAYSCALE)
    object_erased = cv2.imread(str(tmp_path / "object_erased.png"), cv2.IMREAD_GRAYSCALE)

    assert metadata["final_selected_stage"] == "stamp_object_erased"
    assert metadata["ocr_input_source_stage"] == "stamp_object_erased"
    assert metadata["final_selection_reason"] == "lowest_stamp_residual_with_safe_text_preservation"
    assert np.array_equal(final, object_erased)
    assert metadata["candidate_scores"]["stamp_object_erased"]["safe_text_preservation"] is True


def test_text_enhancement_residual_amplification_is_scored_and_not_selected(tmp_path) -> None:
    image, red, protection = _candidate_page()
    amplified = image.copy()
    amplified[75:125, 95:225] = 80
    assert cv2.imwrite(str(tmp_path / "text_enhanced.png"), amplified)

    metadata = _run(
        tmp_path,
        image,
        red,
        protection,
        candidate_paths={"text_enhanced": tmp_path / "text_enhanced.png"},
    )
    scores = metadata["candidate_scores"]

    assert scores["text_enhanced"]["stamp_residual_score"] > scores["stamp_object_erased"]["stamp_residual_score"]
    assert metadata["final_selected_stage"] != "text_enhanced"
    assert metadata["text_enhance_exclude_stamp_mask"] is True


def test_blank_candidate_with_low_residual_is_rejected_for_text_loss(tmp_path) -> None:
    image, red, protection = _candidate_page()
    blank = np.full_like(image, 255)
    assert cv2.imwrite(str(tmp_path / "blank.png"), blank)

    metadata = _run(
        tmp_path,
        image,
        red,
        protection,
        candidate_paths={"unsafe_blank": tmp_path / "blank.png"},
    )

    assert metadata["candidate_scores"]["unsafe_blank"]["safe_text_preservation"] is False
    assert metadata["final_selected_stage"] == "stamp_object_erased"


def _candidate_page():
    image = np.full((200, 320), 250, dtype=np.uint8)
    for y in (25, 42, 158, 175):
        image[y : y + 5, 25:285] = 25
    image[75:125, 95:225] = 205
    red = np.zeros_like(image)
    cv2.rectangle(red, (95, 75), (225, 125), 255, 3)
    protection = np.zeros_like(image)
    for y in (25, 42, 158, 175):
        protection[y : y + 5, 25:285] = 255
    return image, red, protection


def _run(tmp_path, image, red, protection, *, candidate_paths=None):
    for name, value in (("image", image), ("red", red), ("protection", protection)):
        assert cv2.imwrite(str(tmp_path / f"{name}.png"), value)
    return suppress_stamp_for_ocr(
        tmp_path / "image.png", tmp_path / "red.png", tmp_path / "protection.png",
        tmp_path / "ocr_input.png", tmp_path / "suppression.png",
        mode="balanced", erase_mode="component_white_fill",
        object_seed_mask_path=tmp_path / "seed.png",
        stamp_object_mask_path=tmp_path / "object.png",
        stamp_object_erased_path=tmp_path / "object_erased.png",
        final_selected_path=tmp_path / "final.png",
        candidate_paths=candidate_paths,
    )
