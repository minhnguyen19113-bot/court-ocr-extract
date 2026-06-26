from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from court_ocr_extract.models import OcrPage


def draw_bbox_overlay(image_path: str | Path, page: OcrPage, output_path: str | Path) -> Path:
    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        for index, line in enumerate(page.lines, start=1):
            if len(line.bbox) != 4:
                continue
            x0, y0, x1, y1 = line.bbox
            draw.rectangle([x0, y0, x1, y1], outline="red", width=2)
            label = f"{index}"
            draw.rectangle([x0, max(0, y0 - 12), x0 + 28, y0], fill="red")
            draw.text((x0 + 2, max(0, y0 - 11)), label, fill="white", font=font)
        image.save(output_path)
    return output_path
