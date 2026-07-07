from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from court_ocr_extract.ocr_cache import write_ocr_cache_record
from court_ocr_extract.review_html import write_ocr_review, write_run_index
from court_ocr_extract.vlm_backends.fake_vlm import FakeVLMBackend
from court_ocr_extract.vlm_page_reader import read_images_with_vlm


RUN_ID = "vlm_synthetic_smoke"
CASE_ID = "case_001_vlm_synthetic"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create safe synthetic VLM debug outputs.")
    parser.add_argument("--output-root", default="outputs")
    parser.add_argument("--synthetic-root", default="data/synthetic/vlm_smoke")
    args = parser.parse_args(argv)
    result = run_smoke(output_root=Path(args.output_root), synthetic_root=Path(args.synthetic_root))
    print("VLM synthetic smoke finished")
    print(f"Manifest: {result['manifest_path']}")
    print(f"Page markdown: {result['page_markdown_path']}")
    print(f"Combined text: {result['combined_text_path']}")
    print(f"Debug HTML: {result['debug_html_path']}")


def run_smoke(*, output_root: Path, synthetic_root: Path) -> dict[str, str]:
    paths = _paths(output_root, synthetic_root)
    for directory in paths["directories"]:
        directory.mkdir(parents=True, exist_ok=True)

    failed_steps: list[str] = []
    warnings: list[str] = []
    try:
        _create_synthetic_image(paths["synthetic_image"])
        record = read_images_with_vlm(
            [paths["synthetic_image"]],
            case_id=CASE_ID,
            source_index=1,
            pdf_hash="synthetic-vlm-smoke",
            output_dir=paths["debug_dir"],
            backend=FakeVLMBackend(),
        )
        cache_path = write_ocr_cache_record(record, paths["ocr_cache_dir"])
        warnings.extend(record.result.warnings)
        review = write_ocr_review(paths["ocr_review"], [record], base_dir=paths["debug_dir"])
        index = write_run_index(paths["debug_dir"], {"VLM page review": review})
        for step_name, path in [
            ("synthetic_image", paths["synthetic_image"]),
            ("page_markdown", paths["page_markdown"]),
            ("combined_text", paths["combined_text"]),
            ("ocr_cache", cache_path),
            ("debug_html", index),
        ]:
            if not Path(path).exists():
                failed_steps.append(step_name)
    except Exception as exc:  # pragma: no cover - manifest is useful for manual runs.
        failed_steps.append(f"{type(exc).__name__}: {exc}")

    manifest = {
        "run_id": RUN_ID,
        "real_data_accessed": False,
        "provider": "fake",
        "model_name": "fake-vlm-contract",
        "pages_processed": 0 if failed_steps else 1,
        "output_paths": {
            "debug_dir": str(paths["debug_dir"]),
            "page_markdown": str(paths["page_markdown"]),
            "combined_text": str(paths["combined_text"]),
            "ocr_cache": str(paths["ocr_cache_dir"] / f"{CASE_ID}.json"),
            "debug_html": str(paths["debug_dir"] / "index.html"),
        },
        "warnings": warnings,
        "failed_steps": failed_steps,
    }
    paths["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if failed_steps:
        raise SystemExit(1)
    return {
        "manifest_path": str(paths["manifest"]),
        "page_markdown_path": str(paths["page_markdown"]),
        "combined_text_path": str(paths["combined_text"]),
        "debug_html_path": str(paths["debug_dir"] / "index.html"),
    }


def _paths(output_root: Path, synthetic_root: Path) -> dict[str, Any]:
    debug_dir = output_root / "debug_visual" / RUN_ID
    return {
        "directories": [
            synthetic_root,
            debug_dir,
            output_root / "ocr_cache" / RUN_ID,
        ],
        "synthetic_image": debug_dir / "page_001.png",
        "debug_dir": debug_dir,
        "ocr_cache_dir": output_root / "ocr_cache" / RUN_ID,
        "page_markdown": debug_dir / "page_001.md",
        "combined_text": debug_dir / "combined_vlm_text.md",
        "ocr_review": debug_dir / "vlm_page_review.html",
        "manifest": debug_dir / "manifest.json",
    }


def _create_synthetic_image(path: Path) -> None:
    image = Image.new("RGB", (960, 1280), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "TOA AN NHAN DAN - CONTRACT FIXTURE",
        "So: 01/2026/DS-ST",
        "Ngay 01 thang 01 nam 2026",
        "Nguyen don: Nguoi Tham Gia A, sinh nam 1980",
        "Bi don: Nguoi Tham Gia B, sinh nam 1985",
        "NOI DUNG VU AN",
    ]
    y = 80
    for line in lines:
        draw.text((80, y), line, fill="black")
        y += 48
    image.save(path)


if __name__ == "__main__":
    main()
