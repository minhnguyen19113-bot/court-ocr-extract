from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.file_utils import safe_stem, write_json
from court_ocr_extract.image_processing.preprocess import preprocess_for_ocr
from court_ocr_extract.models import model_to_dict
from court_ocr_extract.ocr.marker_detector import detect_marker_in_page
from court_ocr_extract.ocr.surya_adapter import MockOcrEngine, SuryaOcrEngine
from court_ocr_extract.overlay import draw_bbox_overlay
from court_ocr_extract.pdf.render import render_pdf_page
from court_ocr_extract.pdf.validate_pdf import validate_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chọn ngẫu nhiên PDF do người dùng cung cấp, OCR bbox để debug. Codex không tự chạy script này trên dữ liệu thật."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--max-pages-before-marker", "--max-scan-pages", type=int, default=3)
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--remove-red-stamp", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    pdf_paths = sorted(args.input_dir.glob("*.pdf"))
    random.seed(args.seed)
    selected = random.sample(pdf_paths, min(args.sample_size, len(pdf_paths)))
    engine = MockOcrEngine() if settings.enable_mock_ocr else SuryaOcrEngine(settings.surya_language_list)

    for pdf_path in selected:
        page_count = validate_pdf(pdf_path)
        stem = safe_stem(pdf_path.name)
        for page_number in range(1, min(args.max_pages_before_marker, page_count) + 1):
            rendered = render_pdf_page(pdf_path, page_number, settings.bbox_debug_dir / stem / "images", dpi=args.dpi)
            processed = preprocess_for_ocr(
                rendered.image_path,
                settings.bbox_debug_dir / stem / "processed" / rendered.image_path.name,
                remove_red_stamp=args.remove_red_stamp,
            )
            page = engine.ocr_page(processed, page_number=page_number)
            json_path = settings.bbox_debug_dir / f"{stem}_page_{page_number:03d}_bbox.json"
            write_json(json_path, model_to_dict(page))
            overlay_path = settings.bbox_debug_dir / f"{stem}_page_{page_number:03d}_overlay.png"
            draw_bbox_overlay(processed, page, overlay_path)
            marker = detect_marker_in_page(page, marker=settings.section_marker)
            print(f"OK file={stem} page={page_number} marker_found={marker.found}")
            if marker.found:
                break


if __name__ == "__main__":
    main()
