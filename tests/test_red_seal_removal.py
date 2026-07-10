from __future__ import annotations

import pytest
from PIL import Image, ImageDraw

from court_ocr_extract.image_processing.red_stamp_removal import reduce_red_stamp_with_metadata


def test_red_mask_removes_red_but_preserves_black_text(tmp_path) -> None:
    source = tmp_path / "color_page.png"
    output = tmp_path / "seal_removed.png"
    mask = tmp_path / "red_mask.png"
    image = _page_with_lines()
    draw = ImageDraw.Draw(image)
    draw.ellipse((270, 120, 350, 200), outline=(220, 20, 20), width=8)
    image.save(source)

    result = reduce_red_stamp_with_metadata(source, output, mask_path=mask)

    before_red = _count_red(source)
    after_red = _count_red(output)
    assert result.red_pixels_count > 0
    assert result.red_seal_removed is True
    assert result.red_pixels_ratio > 0
    assert mask.exists()
    assert after_red < before_red * 0.1
    assert _count_dark(output) >= _count_dark(source) * 0.95


def test_page_without_red_seal_is_unchanged_and_does_not_fail(tmp_path) -> None:
    source = tmp_path / "plain_page.png"
    output = tmp_path / "plain_after.png"
    _page_with_lines().save(source)

    result = reduce_red_stamp_with_metadata(source, output, mask_path=tmp_path / "mask.png")

    assert result.red_pixels_count == 0
    assert result.red_seal_removed is False
    assert "red_seal_not_detected" in result.warnings
    assert _count_dark(output) == _count_dark(source)


@pytest.mark.parametrize("mode", ["neutralize", "inpaint", "white_fill"])
def test_all_red_removal_modes_reduce_residual_without_blank(tmp_path, mode) -> None:
    source = tmp_path / f"source_{mode}.png"
    output = tmp_path / f"output_{mode}.png"
    image = _page_with_lines()
    ImageDraw.Draw(image).ellipse((270, 120, 350, 200), outline=(205, 55, 55), width=10)
    image.save(source)

    result = reduce_red_stamp_with_metadata(source, output, mode=mode)

    assert result.red_removal_mode == mode
    assert result.red_mask_method == "hsv+lab+rgb"
    assert result.red_mask_components >= 1
    assert result.red_removed_ratio > 0.75
    assert result.red_residual_ratio_estimate < result.red_pixels_ratio
    assert _count_red(output) < _count_red(source) * 0.25
    assert _count_dark(output) > 0


def test_overlap_uses_black_text_protection_and_warns(tmp_path) -> None:
    source = tmp_path / "overlap.png"
    output = tmp_path / "overlap_after.png"
    protection = tmp_path / "black_text_protection.png"
    image = Image.new("RGB", (360, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((120, 65, 245, 190), outline=(220, 30, 30), width=12)
    draw.rectangle((45, 120, 310, 128), fill="black")
    image.save(source)

    result = reduce_red_stamp_with_metadata(
        source,
        output,
        mode="white_fill",
        black_text_protection_path=protection,
    )

    assert protection.exists()
    assert result.dark_text_overlap_ratio > 0
    assert "red_mask_overlaps_dark_text" in result.warnings
    with Image.open(output).convert("L") as after:
        protected_line = [after.getpixel((x, 124)) for x in range(60, 300)]
    assert sum(value < 50 for value in protected_line) > 180


def _page_with_lines() -> Image.Image:
    image = Image.new("RGB", (420, 260), "white")
    draw = ImageDraw.Draw(image)
    for y in range(35, 205, 24):
        draw.rectangle((35, y, 250, y + 5), fill="black")
    return image


def _count_red(path) -> int:
    with Image.open(path).convert("RGB") as image:
        return sum(1 for r, g, b in image.getdata() if r > 140 and r > g * 1.5 and r > b * 1.5)


def _count_dark(path) -> int:
    with Image.open(path).convert("L") as image:
        return sum(1 for value in image.getdata() if value < 80)
