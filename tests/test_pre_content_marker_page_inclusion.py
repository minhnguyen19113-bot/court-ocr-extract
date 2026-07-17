from __future__ import annotations

import pytest

from court_ocr_extract.extractors.pre_content_segmenter import segment_pre_content
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult


@pytest.mark.parametrize("marker_page", [4, 8])
def test_marker_page_keeps_every_line_strictly_before_heading(marker_page: int) -> None:
    rows = []
    for page_number in range(1, marker_page + 1):
        rows.append((page_number, f"Dòng pre-content synthetic trang {page_number}"))
    rows.extend(
        [
            (marker_page, "NỘI DUNG VỤ ÁN"),
            (marker_page, "Dòng synthetic sau marker"),
        ]
    )

    segment = segment_pre_content(_result(rows), max_fallback_pages=3)

    assert segment["end_page"] == marker_page
    assert {line["page_number"] for line in segment["pre_content_lines"]} == set(
        range(1, marker_page + 1)
    )
    assert "Dòng synthetic sau marker" not in segment["pre_content_text"]


def test_missing_marker_uses_configured_fallback_page_limit() -> None:
    rows = [(page, f"Dòng synthetic trang {page}") for page in range(1, 6)]

    segment = segment_pre_content(_result(rows), max_fallback_pages=3)

    assert segment["end_page"] == 3
    assert {line["page_number"] for line in segment["pre_content_lines"]} == {1, 2, 3}
    assert "pre_content_stop_heading_not_found_using_page_limit" in segment["warnings"]


def _result(rows: list[tuple[int, str]]) -> OCRResult:
    pages: dict[int, list[dict[str, object]]] = {}
    for page_number, text in rows:
        lines = pages.setdefault(page_number, [])
        lines.append(
            {
                "line_id": f"p{page_number:03d}_l{len(lines) + 1:04d}",
                "page_number": page_number,
                "text": text,
            }
        )
    return OCRResult(
        backend="synthetic",
        status="success",
        pages_processed=len(pages),
        marker_found=True,
        marker_page=max(pages),
        text="\n".join(text for _, text in rows),
        pages=[
            OCRPage(page_index=page, lines=lines)
            for page, lines in sorted(pages.items())
        ],
    )
