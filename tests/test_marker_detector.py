from court_ocr_extract.models import OcrLine, OcrPage
from court_ocr_extract.ocr.marker_detector import detect_marker_in_page, trim_page_above_marker


def test_detect_marker_and_trim_lines_above_marker():
    page = OcrPage(
        page_number=2,
        lines=[
            OcrLine(text="Bị cáo: Người Tham Gia A", page_number=2, bbox=[0, 10, 100, 20]),
            OcrLine(text="NỘI DUNG VỤ ÁN", page_number=2, bbox=[0, 30, 100, 40]),
            OcrLine(text="Không dùng dòng này", page_number=2, bbox=[0, 50, 100, 60]),
        ],
    )

    marker = detect_marker_in_page(page, marker="NỘI DUNG VỤ ÁN")
    trimmed = trim_page_above_marker(page, marker)

    assert marker.found is True
    assert trimmed.page_text == "Bị cáo: Người Tham Gia A"
    assert len(trimmed.lines) == 1
