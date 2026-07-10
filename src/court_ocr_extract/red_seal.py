from __future__ import annotations

from pathlib import Path

from PIL import Image

from court_ocr_extract.image_processing.red_stamp_removal import reduce_red_stamp_with_metadata


def remove_red_seal_debug(input_path: str | Path, output_dir: str | Path) -> dict[str, Path]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    before = output_dir / "before.png"
    mask = output_dir / "red_mask.png"
    protection = output_dir / "black_text_protection_mask.png"
    after = output_dir / "after.png"
    with Image.open(input_path) as image:
        image.convert("RGB").save(before)
    reduce_red_stamp_with_metadata(
        input_path,
        after,
        mode="neutralize",
        mask_path=mask,
        black_text_protection_path=protection,
    )
    return {
        "before": before,
        "red_mask": mask,
        "black_text_protection_mask": protection,
        "after": after,
    }
