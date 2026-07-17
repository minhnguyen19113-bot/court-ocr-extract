from __future__ import annotations

import inspect

import court_ocr_extract.cli as cli_module
import court_ocr_extract.decision_tail as decision_tail_module
import pytest
from court_ocr_extract.decision_tail import scan_decision_tail
from court_ocr_extract.ocr_backends.base import OCRPage, OCRResult


def test_reverse_scan_stops_after_batch_containing_decision_heading() -> None:
    calls: list[list[int]] = []

    def fake_ocr_batch(page_numbers: list[int]) -> OCRResult:
        calls.append(page_numbers)
        pages = []
        for page_number in page_numbers:
            texts = [f"Dòng synthetic trang {page_number}"]
            if page_number == 6:
                texts.extend(["QUYẾT ĐỊNH", "Tuyên nội dung synthetic"])
            lines = [
                {
                    "line_id": f"p{page_number:03d}_l{index:04d}",
                    "page_number": page_number,
                    "reading_order": index - 1,
                    "text": text,
                }
                for index, text in enumerate(texts, start=1)
            ]
            pages.append(OCRPage(page_index=page_number, lines=lines))
        return OCRResult(
            backend="synthetic",
            status="success",
            pages_processed=len(pages),
            marker_found=False,
            marker_page=None,
            text="",
            pages=pages,
        )

    record = scan_decision_tail(
        case_id="synthetic_case",
        source_index=1,
        pdf_hash="synthetic_hash",
        backend="synthetic",
        pages_total=10,
        ocr_batch=fake_ocr_batch,
        batch_size=2,
        max_scan_pages=8,
    )

    assert calls == [[9, 10], [7, 8], [5, 6]]
    assert record.heading_found is True
    assert record.heading_page == 6
    assert record.text.startswith("QUYẾT ĐỊNH")
    assert "Dòng synthetic trang 5" not in record.text
    assert "Dòng synthetic trang 10" in record.text


def test_reverse_scan_guard_warns_without_heading() -> None:
    def fake_ocr_batch(page_numbers: list[int]) -> OCRResult:
        return OCRResult(
            backend="synthetic",
            status="success",
            pages_processed=len(page_numbers),
            marker_found=False,
            marker_page=None,
            text="",
            pages=[
                OCRPage(
                    page_index=page,
                    lines=[{"line_id": f"p{page:03d}_l0001", "text": "Dòng synthetic"}],
                )
                for page in page_numbers
            ],
        )

    record = scan_decision_tail(
        case_id="synthetic_case",
        source_index=1,
        pdf_hash=None,
        backend="synthetic",
        pages_total=9,
        ocr_batch=fake_ocr_batch,
        batch_size=2,
        max_scan_pages=2,
    )

    assert record.heading_found is False
    assert record.text == ""
    assert "decision_heading_not_found_within_scan_limit" in record.warnings


def test_decision_tail_module_has_no_case_specific_page_or_file_allowlist() -> None:
    source = inspect.getsource(decision_tail_module)

    assert "case_001" not in source
    assert ".pdf" not in source
    assert "page_22" not in source and "page_26" not in source


def test_decision_tail_cli_refuses_non_surya_backend(monkeypatch) -> None:
    class FakeLegacyBackend:
        name = "tesseract"

    monkeypatch.setattr(
        cli_module,
        "get_ocr_backend",
        lambda *_args, **_kwargs: FakeLegacyBackend(),
    )

    with pytest.raises(RuntimeError, match="only supports the Surya OCR backend"):
        cli_module.main(
            [
                "ocr-decision-tail",
                "--input-dir",
                "synthetic_input",
                "--ocr-cache-dir",
                "synthetic_cache",
                "--output-dir",
                "synthetic_output",
                "--ocr-backend",
                "tesseract",
            ]
        )
