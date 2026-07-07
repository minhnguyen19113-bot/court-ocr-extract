from __future__ import annotations

from pathlib import Path

from PIL import Image

from court_ocr_extract.image_processing.red_stamp_removal import reduce_red_stamp


def remove_red_seal_debug(input_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    before = output_dir / "before.png"
    mask = output_dir / "red_mask.png"
    after = output_dir / "after.png"
    Image.open(input_path).save(before)
    _write_red_mask(input_path, mask)
    reduce_red_stamp(input_path, after)
    return {"before": before, "red_mask": mask, "after": after}


def _write_red_mask(input_path: Path, output_path: Path) -> None:
    with Image.open(input_path).convert("RGB") as image:
        mask = Image.new("L", image.size, 0)
        source = image.load()
        target = mask.load()
        for y in range(image.height):
            for x in range(image.width):
                r, g, b = source[x, y]
                if r > 120 and r > g * 1.25 and r > b * 1.25:
                    target[x, y] = 255
        mask.save(output_path)
