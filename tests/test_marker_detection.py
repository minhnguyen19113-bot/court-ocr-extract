from __future__ import annotations

from court_ocr_extract.marker_detection import detect_page_marker, normalize_marker_text
from court_ocr_extract.settings import DEFAULT_STOP_MARKER


def test_exact_marker_is_high_confidence() -> None:
    result = detect_page_marker(
        page_number=6,
        marker_text=DEFAULT_STOP_MARKER,
        filtered_lines=[{"text": "NỘI DUNG VỤ ÁN"}],
        page_text="NỘI DUNG VỤ ÁN",
    )

    assert result.found is True
    assert result.should_stop is True
    assert result.confidence == "high"
    assert result.page_number == 6
    assert result.normalized_match == "noi dung vu an"


def test_no_diacritic_and_noisy_spacing_markers_are_detected() -> None:
    plain = detect_page_marker(
        page_number=1,
        marker_text=DEFAULT_STOP_MARKER,
        page_text="NOI DUNG VU AN",
    )
    noisy = detect_page_marker(
        page_number=2,
        marker_text=DEFAULT_STOP_MARKER,
        page_text="N Ộ I   D U N G   V Ụ   Á N",
    )

    assert plain.confidence == "high"
    assert noisy.confidence == "high"
    assert normalize_marker_text("NỘI DUNG VỤ ÁN") == "noi dung vu an"


def test_marker_split_across_lines_and_filtered_only_is_detected() -> None:
    result = detect_page_marker(
        page_number=3,
        marker_text=DEFAULT_STOP_MARKER,
        raw_lines=[{"text": "synthetic header"}],
        filtered_lines=[{"text": "NỘI DUNG"}, {"text": "VỤ ÁN"}],
        page_text="NỘI DUNG\nVỤ ÁN",
    )

    assert result.should_stop is True
    assert result.source == "filtered_lines"
    assert result.line_index == 0


def test_truncated_marker_is_medium_but_noi_dung_alone_does_not_stop() -> None:
    medium = detect_page_marker(
        page_number=1,
        marker_text=DEFAULT_STOP_MARKER,
        page_text="NỘI DUNG VỤ Á",
    )
    low = detect_page_marker(
        page_number=1,
        marker_text=DEFAULT_STOP_MARKER,
        page_text="NỘI DUNG",
    )

    assert medium.confidence == "medium"
    assert medium.should_stop is True
    assert low.confidence == "low"
    assert low.should_stop is False


def test_text_before_marker_trims_same_page_content() -> None:
    result = detect_page_marker(
        page_number=1,
        marker_text=DEFAULT_STOP_MARKER,
        page_text="synthetic pre-content\nNỘI DUNG VỤ ÁN\nsynthetic body",
    )

    assert result.before_text == "synthetic pre-content"
    assert "synthetic body" not in result.before_text

