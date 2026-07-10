from __future__ import annotations

from PIL import Image, ImageDraw, ImageStat

from court_ocr_extract.image_processing import preprocess as preprocess_module
from court_ocr_extract.image_preprocess import preprocess_image


def test_light_text_enhancement_darkens_faint_text_without_explosion(tmp_path) -> None:
    source = tmp_path / "faint_text.png"
    output = tmp_path / "final.png"
    text_stage = tmp_path / "text_enhanced.png"
    image = Image.new("RGB", (480, 260), "white")
    draw = ImageDraw.Draw(image)
    for y in range(45, 205, 26):
        draw.rectangle((45, y, 420, y + 4), fill=(145, 145, 145))
    image.save(source)
    metadata = {}

    preprocess_image(
        source,
        output,
        text_enhance_mode="light",
        text_enhanced_path=text_stage,
        metadata=metadata,
    )

    assert text_stage.exists()
    assert metadata["text_enhance_mode"] == "light"
    assert "text_enhance_guard_triggered" not in metadata["warnings"]
    assert metadata["foreground_after_enhance"] < metadata["foreground_before_enhance"] * 2.5
    assert _region_mean(text_stage, (45, 45, 420, 205)) < _region_mean(source, (45, 45, 420, 205))


def test_strong_text_enhancement_guard_falls_back_on_dark_explosion(tmp_path, monkeypatch) -> None:
    source = tmp_path / "content.png"
    output = tmp_path / "final.png"
    _page_with_black_text().save(source)

    def explode(gray, mode, cv2, np):
        return np.zeros_like(gray)

    monkeypatch.setattr(preprocess_module, "_enhance_black_text", explode)
    metadata = {}
    preprocess_image(source, output, text_enhance_mode="strong", metadata=metadata)

    assert "text_enhance_guard_triggered" in metadata["warnings"]
    assert "dark_pixel_explosion" in metadata["warnings"]
    assert metadata["fallback_source"] == "original"
    with Image.open(output).convert("L") as image:
        assert ImageStat.Stat(image).mean[0] > 200


def test_blank_page_remains_valid_blank_without_guard_warning(tmp_path) -> None:
    source = tmp_path / "blank.png"
    output = tmp_path / "blank_final.png"
    Image.new("RGB", (360, 240), "white").save(source)
    metadata = {}

    preprocess_image(
        source,
        output,
        remove_red_seal=True,
        text_enhance_mode="light",
        metadata=metadata,
    )

    assert metadata["blank_guard_triggered"] is False
    assert "text_enhance_guard_triggered" not in metadata["warnings"]
    assert "foreground_loss_too_high" not in metadata["warnings"]
    assert _region_mean(output, (0, 0, 360, 240)) > 250


def test_preprocess_writes_all_red_and_text_debug_artifacts(tmp_path) -> None:
    source = tmp_path / "source.png"
    output = tmp_path / "final.png"
    image = _page_with_black_text()
    ImageDraw.Draw(image).ellipse((280, 130, 390, 235), outline=(220, 25, 25), width=9)
    image.save(source)
    artifacts = {
        "seal": tmp_path / "seal_removed.png",
        "mask": tmp_path / "red_mask.png",
        "protection": tmp_path / "black_text_protection_mask.png",
        "text": tmp_path / "text_enhanced.png",
    }
    metadata = {}

    preprocess_image(
        source,
        output,
        remove_red_seal=True,
        intermediate_path=artifacts["seal"],
        red_mask_path=artifacts["mask"],
        black_text_protection_path=artifacts["protection"],
        red_removal_mode="neutralize",
        text_enhanced_path=artifacts["text"],
        text_enhance_mode="light",
        metadata=metadata,
    )

    assert output.exists()
    assert all(path.exists() for path in artifacts.values())
    assert metadata["red_removal_mode"] == "neutralize"
    assert metadata["text_enhance_mode"] == "light"
    assert isinstance(metadata["warnings"], list)


def _page_with_black_text() -> Image.Image:
    image = Image.new("RGB", (480, 280), "white")
    draw = ImageDraw.Draw(image)
    for y in range(45, 225, 25):
        draw.rectangle((45, y, 420, y + 5), fill="black")
    return image


def _region_mean(path, box) -> float:
    with Image.open(path).convert("L") as image:
        return float(ImageStat.Stat(image.crop(box)).mean[0])
