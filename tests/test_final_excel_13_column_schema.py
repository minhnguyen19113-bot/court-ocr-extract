from __future__ import annotations

from court_ocr_extract.final_excel_schema import FINAL_EXCEL_COLUMNS


def test_final_excel_has_exact_canonical_14_column_order() -> None:
    assert FINAL_EXCEL_COLUMNS == [
        "LOẠI ÁN",
        "SỐ BẢN ÁN",
        "NGÀY TUYÊN ÁN (DD/MM/YYYY)",
        "SỐ THỤ LÝ",
        "NGÀY THỤ LÝ (DD/MM/YYYY)",
        "QUAN HỆ PHÁP LUẬT",
        "HÌNH PHẠT",
        "TƯ CÁCH TỐ TỤNG",
        "HỌ TÊN ĐƯƠNG SỰ",
        "NĂM SINH",
        "CCCD",
        "ĐỊA CHỈ",
        "HỌ TÊN CHỦ TỌA",
        "GHI CHÚ",
    ]
