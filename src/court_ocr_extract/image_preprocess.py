from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from court_ocr_extract.image_processing.preprocess import preprocess_for_ocr


def preprocess_image(
    input_path: str | Path,
    output_path: str | Path,
    *,
    remove_red_seal: bool = False,
    intermediate_path: str | Path | None = None,
    red_mask_path: str | Path | None = None,
    deskew_mode: str = "off",
    preprocess_profile: str = "conservative",
    metadata: dict[str, Any] | None = None,
) -> Path:
    return preprocess_for_ocr(
        input_path,
        output_path,
        remove_red_stamp=remove_red_seal,
        intermediate_path=intermediate_path,
        red_mask_path=red_mask_path,
        deskew_mode=deskew_mode,
        preprocess_profile=preprocess_profile,
        metadata=metadata,
    )


def make_before_after_compare(before_path: str | Path, after_path: str | Path, output_path: str | Path) -> Path:
    before_path = Path(before_path)
    after_path = Path(after_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(before_path).convert("RGB") as before, Image.open(after_path).convert("RGB") as after:
        height = max(before.height, after.height)
        before_resized = _fit_height(before, height)
        after_resized = _fit_height(after, height)
        gutter = 16
        canvas = Image.new("RGB", (before_resized.width + after_resized.width + gutter, height), "white")
        canvas.paste(before_resized, (0, 0))
        canvas.paste(after_resized, (before_resized.width + gutter, 0))
        canvas = ImageOps.expand(canvas, border=1, fill=(210, 210, 210))
        canvas.save(output_path)
    return output_path


def _fit_height(image: Image.Image, height: int) -> Image.Image:
    if image.height == height:
        return image
    width = max(1, int(image.width * (height / image.height)))
    return image.resize((width, height))
