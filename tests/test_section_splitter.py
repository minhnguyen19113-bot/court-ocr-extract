from court_ocr_extract.postprocess.section_splitter import split_before_marker


def test_split_before_marker_fuzzy():
    text = "Dòng đầu\nNỘI DƯNG VỤ ÁN\nDòng sau"

    split = split_before_marker(text, marker="NỘI DUNG VỤ ÁN")

    assert split.marker.found is True
    assert split.before_text == "Dòng đầu"
    assert "Dòng sau" in split.after_text


def test_split_before_marker_accepts_unaccented_ocr():
    text = "Dòng đầu\nNOI DUNG VU AN:\nDòng sau"

    split = split_before_marker(text, marker="NỘI DUNG VỤ ÁN")

    assert split.marker.found is True
    assert split.before_text == "Dòng đầu"


def test_split_before_marker_accepts_common_extra_word():
    text = "Dòng đầu\nNỘI DUNG CỦA VỤ ÁN\nDòng sau"

    split = split_before_marker(text, marker="NỘI DUNG VỤ ÁN")

    assert split.marker.found is True
    assert split.before_text == "Dòng đầu"
