from court_ocr_extract.excel import rows_from_result
from court_ocr_extract.extractor import extract_rule_based
from court_ocr_extract.normalizer import find_noi_dung_marker
from court_ocr_extract.validator import validate_extraction


FAKE_JUDGMENT_TEXT = """
TÒA ÁN NHÂN DÂN HUYỆN A
BẢN ÁN HÌNH SỰ SƠ THẨM
Vụ án hình sự thụ lý số: 12/2025/TLST-HS ngày 03 tháng 04 năm 2025 về tội "Trộm cắp tài sản".
Thẩm phán - Chủ tọa phiên tòa: Người Chủ Tọa
Bị cáo: Người Tham Gia A, sinh năm 1990; CCCD số 012345678901; nơi cư trú: thôn Một, xã Hai, huyện Ba, tỉnh C.
Bị hại: Bà Người Tham Gia B, sinh năm 1985; CMND số 123456789; địa chỉ: phường X, quận Y, thành phố Z.
Người có quyền lợi, nghĩa vụ liên quan: Ông Người Tham Gia C, sinh ngày 01/02/1978; nơi cư trú: xã M, huyện N, tỉnh P.
NỘI DƯNG VỤ ÁN
Bị cáo: Người Sau Marker, sinh năm 2000; địa chỉ: không được trích xuất.
"""


def test_fuzzy_marker_noi_dung_vu_an():
    marker = find_noi_dung_marker("abc\nNỘI DƯNG VỤ ÁN\nxyz")

    assert marker.found is True
    assert marker.score >= 82


def test_rule_extractor_case_info_and_participants():
    result = validate_extraction(extract_rule_based(FAKE_JUDGMENT_TEXT, source_file="fake.pdf"))

    assert result.marker_found is True
    assert result.case_info.loai_an == "Hình sự"
    assert result.case_info.so_thu_ly == "12/2025/TLST-HS"
    assert result.case_info.ngay_thu_ly == "03/04/2025"
    assert result.case_info.quan_he_phap_luat == "Trộm cắp tài sản"
    assert result.case_info.chu_toa == "Người Chủ Tọa"

    assert [person.tu_cach_to_tung for person in result.participants] == [
        "Bị cáo",
        "Bị hại",
        "Người có quyền lợi, nghĩa vụ liên quan",
    ]
    assert result.participants[0].ho_ten == "Người Tham Gia A"
    assert result.participants[0].nam_sinh == "1990"
    assert result.participants[0].cccd == "012345678901"
    assert "thôn Một" in result.participants[0].dia_chi
    assert all(person.ho_ten != "Người Sau Marker" for person in result.participants)


def test_excel_rows_repeat_case_info_per_person():
    result = validate_extraction(extract_rule_based(FAKE_JUDGMENT_TEXT, source_file="fake.pdf"))
    rows = rows_from_result(result)

    assert len(rows) == 3
    assert all(row["SỐ THỤ LÝ"] == "12/2025/TLST-HS" for row in rows)
    assert rows[1]["TƯ CÁCH TỐ TỤNG"] == "Bị hại"
    assert "EMAIL NGƯỜI NHẬP" not in rows[0]
