from __future__ import annotations

from court_ocr_extract.excel_writer import EXCEL_HEADERS
from court_ocr_extract.final_excel_schema import (
    FINAL_EXCEL_COLUMNS,
    FINAL_EXCEL_SHEET_NAME,
)


EXPECTED_FINAL_COLUMNS = [
    "LOẠI ÁN",
    "SỐ THỤ LÝ",
    "NGÀY THỤ LÝ (DD/MM/YYYY)",
    "QUAN HỆ PHÁP LUẬT",
    "TƯ CÁCH TỐ TỤNG",
    "HỌ TÊN ĐƯƠNG SỰ",
    "NĂM SINH",
    "CCCD",
    "ĐỊA CHỈ",
    "HỌ TÊN CHỦ TỌA",
    "GHI CHÚ",
]


def test_final_excel_schema_has_exactly_eleven_columns_in_owner_order() -> None:
    assert FINAL_EXCEL_SHEET_NAME == "FINAL_EXCEL"
    assert FINAL_EXCEL_COLUMNS == EXPECTED_FINAL_COLUMNS
    assert EXCEL_HEADERS == FINAL_EXCEL_COLUMNS
    assert len(FINAL_EXCEL_COLUMNS) == 11
    assert len(set(FINAL_EXCEL_COLUMNS)) == 11
