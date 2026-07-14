from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_path: Path
    width: int
    height: int


def get_pdf_page_count(pdf_path: str | Path) -> int:
    import fitz

    document = fitz.open(Path(pdf_path))
    try:
        return int(document.page_count)
    finally:
        document.close()


def parse_page_range(value: str | None) -> list[int] | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value.lower() == "all":
        return None
    pages: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return sorted(page for page in pages if page > 0)


def render_pdf_pages(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    dpi: int = 300,
    max_pages: int | None = None,
    page_numbers: list[int] | None = None,
) -> list[RenderedPage]:
    import fitz

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[RenderedPage] = []
    document = fitz.open(pdf_path)
    try:
        if page_numbers is None:
            total = document.page_count if max_pages is None else min(document.page_count, max_pages)
            selected_pages = list(range(1, total + 1))
        else:
            selected_pages = [page for page in page_numbers if 1 <= page <= document.page_count]
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        for page_number in selected_pages:
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_dir / f"page_{page_number:03d}_rendered.png"
            pixmap.save(str(image_path))
            rendered.append(
                RenderedPage(
                    page_number=page_number,
                    image_path=image_path,
                    width=pixmap.width,
                    height=pixmap.height,
                )
            )
    finally:
        document.close()
    return rendered
