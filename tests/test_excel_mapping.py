from court_ocr_extract.export.excel_writer import EXCEL_HEADERS


def test_excel_mapping_contains_requested_columns_only():
    assert EXCEL_HEADERS == [
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
    assert "EMAIL NGƯỜI NHẬP" not in EXCEL_HEADERS
