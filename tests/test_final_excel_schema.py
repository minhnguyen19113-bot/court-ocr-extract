from __future__ import annotations

from court_ocr_extract.excel_writer import EXCEL_HEADERS
from court_ocr_extract.final_excel_schema import (
    FINAL_EXCEL_COLUMNS,
    FINAL_EXCEL_SHEET_NAME,
)


def test_final_excel_schema_uses_canonical_fourteen_column_contract() -> None:
    assert FINAL_EXCEL_SHEET_NAME == "FINAL_EXCEL"
    assert EXCEL_HEADERS == FINAL_EXCEL_COLUMNS
    assert len(FINAL_EXCEL_COLUMNS) == 14
    assert len(set(FINAL_EXCEL_COLUMNS)) == 14
    assert FINAL_EXCEL_COLUMNS.index("HÌNH PHẠT") == (
        FINAL_EXCEL_COLUMNS.index("QUAN HỆ PHÁP LUẬT") + 1
    )
    assert FINAL_EXCEL_COLUMNS[-1] == "GHI CHÚ"
