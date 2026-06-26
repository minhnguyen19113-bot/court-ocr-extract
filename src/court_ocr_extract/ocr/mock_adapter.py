from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from court_ocr_extract.models import OcrLine, OcrPage


class MockOcrAdapter:
    """Synthetic/mock OCR adapter for tests and UI demos without GPU."""

    def __init__(self, page_texts: dict[int, str] | None = None) -> None:
        self.page_texts = page_texts or {}

    def ocr_page(self, image_path: str | Path, page_number: int) -> OcrPage:
        image_path = Path(image_path)
        start = time.perf_counter()
        text = self.page_texts.get(page_number)
        if text is None:
            sidecar = image_path.with_suffix(".txt")
            text = sidecar.read_text(encoding="utf-8") if sidecar.exists() else _default_mock_text(page_number)

        width, height = _image_size(image_path)
        lines = []
        for index, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            top = 40 + index * 34
            lines.append(
                OcrLine(
                    text=line.strip(),
                    page_number=page_number,
                    bbox=[40.0, float(top), 1200.0, float(top + 28)],
                    confidence=0.99,
                )
            )
        return OcrPage(
            page_number=page_number,
            width=width,
            height=height,
            lines=lines,
            text=text,
            ocr_time=time.perf_counter() - start,
            processed_image_path=str(image_path),
        )


def _image_size(path: Path) -> tuple[int | None, int | None]:
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None, None


def _default_mock_text(page_number: int) -> str:
    if page_number == 1:
        return (
            "TÒA ÁN NHÂN DÂN HUYỆN A\n"
            "BẢN ÁN HÌNH SỰ SƠ THẨM\n"
            "Vụ án hình sự thụ lý số: 12/2025/TLST-HS ngày 03 tháng 04 năm 2025.\n"
            "Thẩm phán - Chủ tọa phiên tòa: Người Chủ Tọa\n"
            "Bị cáo: Người Tham Gia A, sinh năm 1990; CCCD số 012345678901; "
            "nơi cư trú: xã B, huyện C.\n"
        )
    if page_number == 2:
        return "NỘI DUNG VỤ ÁN\nPhần này không dùng để bóc tách."
    return ""


MockOcrEngine = MockOcrAdapter
