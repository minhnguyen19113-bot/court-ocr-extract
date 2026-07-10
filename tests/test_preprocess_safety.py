from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from court_ocr_extract.image_processing import preprocess as preprocess_module
from court_ocr_extract.image_preprocess import preprocess_image
from court_ocr_extract.review_html import write_preprocess_review


def test_red_removal_receives_color_source_before_grayscale(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source.png"
    _synthetic_page(with_red=True).save(source)
    observed_modes: list[str] = []
    original = preprocess_module.reduce_red_stamp_with_metadata

    def inspect_color(input_path, *args, **kwargs):
        with Image.open(input_path) as image:
            observed_modes.append(image.mode)
        return original(input_path, *args, **kwargs)

    monkeypatch.setattr(preprocess_module, "reduce_red_stamp_with_metadata", inspect_color)
    metadata = {}
    preprocess_image(
        source,
        tmp_path / "final.png",
        remove_red_seal=True,
        intermediate_path=tmp_path / "seal_removed.png",
        red_mask_path=tmp_path / "red_mask.png",
        metadata=metadata,
    )

    assert observed_modes == ["RGB"]
    assert metadata["red_pixels_count"] > 0


def test_safe_deskew_does_not_rotate_straight_page(tmp_path) -> None:
    source = tmp_path / "straight.png"
    _synthetic_page().save(source)
    metadata = {}

    preprocess_image(source, tmp_path / "final.png", deskew_mode="safe", metadata=metadata)

    assert metadata["deskew_applied"] is False
    assert metadata["detected_angle"] is None or abs(metadata["detected_angle"]) < 0.3


def test_safe_deskew_rotates_only_with_sufficient_evidence(tmp_path) -> None:
    source = tmp_path / "slightly_skewed.png"
    _synthetic_page().rotate(2.0, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white").save(source)
    metadata = {}

    preprocess_image(source, tmp_path / "final.png", deskew_mode="safe", metadata=metadata)

    if metadata["deskew_applied"]:
        assert 0.3 <= abs(metadata["detected_angle"]) <= 5.0
        assert metadata["deskew_confidence"] >= 0.65
        assert metadata["deskew_reason"] == "safe_rotation_high_confidence"
    else:
        assert metadata["deskew_reason"] in {
            "confidence_below_safe_threshold",
            "insufficient_horizontal_evidence",
            "foreground_near_page_edge",
            "ambiguous_multi_column_layout",
        }
        assert any(item.startswith("deskew_skipped") for item in metadata["warnings"])


def test_blank_guard_falls_back_to_previous_safe_image(tmp_path, monkeypatch) -> None:
    source = tmp_path / "content.png"
    output = tmp_path / "final.png"
    _synthetic_page().save(source)

    def blank_profile(gray, profile, cv2):
        import numpy as np

        return np.full_like(gray, 255)

    monkeypatch.setattr(preprocess_module, "_apply_profile", blank_profile)
    metadata = {}
    preprocess_image(source, output, metadata=metadata)

    assert metadata["blank_guard_triggered"] is True
    assert metadata["fallback_source"] == "original"
    assert "preprocess_blank_guard_triggered" in metadata["warnings"]
    assert "foreground_loss_too_high" in metadata["warnings"]
    with Image.open(output).convert("L") as image:
        assert any(value < 80 for value in image.getdata())


def test_preprocess_review_contains_artifacts_and_safety_metadata(tmp_path) -> None:
    original = tmp_path / "original.png"
    final = tmp_path / "final.png"
    _synthetic_page().save(original)
    _synthetic_page().convert("L").save(final)
    output = tmp_path / "review.html"

    write_preprocess_review(
        output,
        base_dir=tmp_path,
        cases=[
            {
                "case_id": "case_synthetic",
                "pages": [
                    {
                        "images": [("original", original), ("final_preprocessed", final)],
                        "metadata": {
                            "page_number": 1,
                            "deskew_mode": "off",
                            "deskew_applied": False,
                            "deskew_reason": "deskew_disabled",
                            "warnings": ["synthetic_warning"],
                        },
                    }
                ],
            }
        ],
    )

    html = output.read_text(encoding="utf-8")
    assert "original" in html
    assert "final_preprocessed" in html
    assert "deskew_disabled" in html
    assert "synthetic_warning" in html


def _synthetic_page(*, with_red: bool = False) -> Image.Image:
    image = Image.new("RGB", (520, 340), "white")
    draw = ImageDraw.Draw(image)
    for y in range(45, 285, 25):
        draw.rectangle((55, y, 450, y + 5), fill="black")
    if with_red:
        draw.ellipse((365, 200, 460, 295), outline=(220, 20, 20), width=8)
    return image
