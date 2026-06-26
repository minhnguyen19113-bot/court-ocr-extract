from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from court_ocr_extract.config import Settings
from court_ocr_extract.file_utils import write_json
from court_ocr_extract.image_processing.preprocess import preprocess_for_ocr
from court_ocr_extract.models import OcrDocument, model_to_dict
from court_ocr_extract.ocr.base import OcrAdapter
from court_ocr_extract.ocr.marker_detector import detect_marker_in_page, trim_page_above_marker
from court_ocr_extract.pdf.render import render_pdf_page


@dataclass(frozen=True)
class EarlyStopConfig:
    dpi: int
    remove_red_stamp: bool
    max_pages_before_marker: int
    stop_on_marker: bool = True
    force_full_ocr: bool = False


class EarlyStopPipeline:
    def __init__(self, settings: Settings, ocr_adapter: OcrAdapter) -> None:
        self.settings = settings
        self.ocr_adapter = ocr_adapter

    def run(
        self,
        *,
        pdf_path: str | Path,
        output_stem: str,
        page_count: int,
        config: EarlyStopConfig,
    ) -> OcrDocument:
        pdf_path = Path(pdf_path)
        image_dir = self.settings.images_dir / output_stem
        processed_dir = self.settings.processed_images_dir / output_stem
        intermediate_dir = self.settings.processed_intermediate_dir / output_stem
        per_page_dir = self.settings.ocr_raw_dir / output_stem
        per_page_dir.mkdir(parents=True, exist_ok=True)

        pages = []
        marker_found = False
        marker_page = None
        marker_position = None
        marker_score = None
        stop_reason = "max_pages_before_content_marker_reached"

        page_limit = page_count if config.force_full_ocr else min(config.max_pages_before_marker, page_count)
        for page_number in range(1, page_limit + 1):
            rendered = render_pdf_page(pdf_path, page_number, image_dir, dpi=config.dpi)
            processed_path = preprocess_for_ocr(
                rendered.image_path,
                processed_dir / rendered.image_path.name,
                remove_red_stamp=config.remove_red_stamp,
                intermediate_path=intermediate_dir / rendered.image_path.name,
            )
            page = self.ocr_adapter.ocr_page(processed_path, page_number=page_number)
            page.image_path = str(rendered.image_path)
            page.processed_image_path = str(processed_path)

            marker_match = detect_marker_in_page(page, marker=self.settings.section_marker)
            if marker_match.found:
                marker_found = True
                marker_page = page_number
                marker_position = marker_match.start
                marker_score = marker_match.score
                if config.stop_on_marker and not config.force_full_ocr:
                    page = trim_page_above_marker(page, marker_match)
                    stop_reason = "content_marker_found"
                    pages.append(page)
                    write_json(per_page_dir / f"page_{page_number:03d}.json", model_to_dict(page))
                    break

            pages.append(page)
            write_json(per_page_dir / f"page_{page_number:03d}.json", model_to_dict(page))

        else:
            if config.force_full_ocr and page_limit >= page_count:
                stop_reason = "force_full_ocr_completed"
            elif page_limit >= page_count:
                stop_reason = "end_of_pdf_without_marker"

        return OcrDocument(
            source_file=pdf_path.name,
            pages=pages,
            stop_reason=stop_reason,
            marker_found=marker_found,
            marker_page=marker_page,
            marker_position=marker_position,
            marker_score=marker_score,
            pages_ocr=len(pages),
        )
