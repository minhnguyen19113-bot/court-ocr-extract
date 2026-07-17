from court_ocr_extract.excel_writer import EXCEL_HEADERS
from court_ocr_extract.final_excel_schema import FINAL_EXCEL_COLUMNS


def test_excel_mapping_contains_requested_columns_only():
    assert EXCEL_HEADERS == FINAL_EXCEL_COLUMNS
    assert len(EXCEL_HEADERS) == 13
    assert "EMAIL NGƯỜI NHẬP" not in EXCEL_HEADERS
