from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from court_ocr_extract.file_utils import safe_stem


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_path: Path
    width: int
    height: int


def render_pdf_page(
    pdf_path: str | Path,
    page_number: int,
    output_dir: str | Path,
    dpi: int = 300,
) -> RenderedPage:
    import fitz

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    document = fitz.open(pdf_path)
    try:
        if page_number < 1 or page_number > document.page_count:
            raise ValueError(f"Page {page_number} is outside PDF range 1..{document.page_count}")
        page = document.load_page(page_number - 1)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = output_dir / f"{safe_stem(pdf_path.name)}_page_{page_number:03d}.png"
        pixmap.save(str(image_path))
        return RenderedPage(
            page_number=page_number,
            image_path=image_path,
            width=pixmap.width,
            height=pixmap.height,
        )
    finally:
        document.close()


def iter_render_pdf_pages(
    pdf_path: str | Path,
    output_dir: str | Path,
    dpi: int = 300,
    max_pages: int | None = None,
) -> Iterator[RenderedPage]:
    import fitz

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    document = fitz.open(pdf_path)
    try:
        total = document.page_count if max_pages is None else min(max_pages, document.page_count)
        for page_index in range(total):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            page_number = page_index + 1
            image_path = output_dir / f"{safe_stem(pdf_path.name)}_page_{page_number:03d}.png"
            pixmap.save(str(image_path))
            yield RenderedPage(
                page_number=page_number,
                image_path=image_path,
                width=pixmap.width,
                height=pixmap.height,
            )
    finally:
        document.close()


def render_pdf_to_images(
    pdf_path: str | Path,
    output_dir: str | Path,
    dpi: int = 300,
    page_numbers: Iterable[int] | None = None,
) -> list[Path]:
    if page_numbers is not None:
        return [
            render_pdf_page(pdf_path, page_number, output_dir, dpi=dpi).image_path
            for page_number in page_numbers
        ]
    return [page.image_path for page in iter_render_pdf_pages(pdf_path, output_dir, dpi=dpi)]
