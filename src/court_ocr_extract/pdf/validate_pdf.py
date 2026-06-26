from __future__ import annotations

from pathlib import Path


class PdfValidationError(RuntimeError):
    pass


def get_pdf_page_count(pdf_path: str | Path) -> int:
    try:
        import fitz
    except Exception as exc:
        raise PdfValidationError("PyMuPDF chưa được cài. Cài bằng `pip install PyMuPDF`.") from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise PdfValidationError(f"Không tìm thấy PDF: {pdf_path}")
    if pdf_path.stat().st_size == 0:
        raise PdfValidationError(f"PDF rỗng: {pdf_path}")
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise PdfValidationError(f"Không mở được PDF: {pdf_path}") from exc
    try:
        page_count = document.page_count
    finally:
        document.close()
    if page_count < 1:
        raise PdfValidationError(f"PDF không có trang: {pdf_path}")
    return page_count


def validate_pdf(pdf_path: str | Path) -> int:
    return get_pdf_page_count(pdf_path)
