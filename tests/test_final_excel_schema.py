from __future__ import annotations

from court_ocr_extract.excel_writer import EXCEL_HEADERS
from court_ocr_extract.final_excel_schema import (
    FINAL_EXCEL_COLUMNS,
    FINAL_EXCEL_SHEET_NAME,
)


def test_final_excel_schema_uses_canonical_thirteen_column_contract() -> None:
    assert FINAL_EXCEL_SHEET_NAME == "FINAL_EXCEL"
    assert EXCEL_HEADERS == FINAL_EXCEL_COLUMNS
    assert len(FINAL_EXCEL_COLUMNS) == 13
    assert len(set(FINAL_EXCEL_COLUMNS)) == 13
