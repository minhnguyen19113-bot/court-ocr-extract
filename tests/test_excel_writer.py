from court_ocr_extract.export.excel_writer import rows_from_result
from court_ocr_extract.models import CaseInfo, ExtractionResult, Participant


def test_excel_rows_repeat_case_info_and_drop_removed_columns():
    result = ExtractionResult(
        case_info=CaseInfo(
            loai_an="Hình sự",
            so_thu_ly="12/2025/TLST-HS",
            ngay_thu_ly="03/04/2025",
            quan_he_phap_luat="Trộm cắp tài sản",
            chu_toa="Người Chủ Tọa",
        ),
        participants=[
            Participant(tu_cach_to_tung="Bị cáo", ho_ten="Người Tham Gia A", nam_sinh="1990"),
            Participant(tu_cach_to_tung="Bị hại", ho_ten="Người Tham Gia B", nam_sinh="1985"),
        ],
    )

    rows = rows_from_result(result)

    assert len(rows) == 2
    assert all(row["SỐ THỤ LÝ"] == "12/2025/TLST-HS" for row in rows)
    assert "EMAIL NGƯỜI NHẬP" not in rows[0]
