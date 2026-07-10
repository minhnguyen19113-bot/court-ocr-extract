from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from court_ocr_extract import cli
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRResult
from court_ocr_extract.pdf_render import parse_page_range


def test_parse_page_range_defaults_to_all_pages() -> None:
    assert parse_page_range(None) is None
    assert parse_page_range("") is None
    assert parse_page_range("all") is None
    assert parse_page_range("  ALL  ") is None
    assert parse_page_range("1-3") == [1, 2, 3]
    assert parse_page_range("2,4,6-8") == [2, 4, 6, 7, 8]


def test_debug_render_without_pages_passes_none_to_render(tmp_path, monkeypatch) -> None:
    captured: list[list[int] | None] = []
    case = _case(tmp_path)
    _stub_review_command(monkeypatch, tmp_path, case)

    def fake_render_pdf_pages(pdf_path, output_dir, *, dpi, page_numbers=None, max_pages=None):
        captured.append(page_numbers)
        return [SimpleNamespace(page_number=1, image_path=tmp_path / "page_001.png")]

    monkeypatch.setattr(cli, "render_pdf_pages", fake_render_pdf_pages)

    cli.main(
        [
            "debug-render",
            "--input",
            str(tmp_path),
            "--limit",
            "1",
            "--review-sample-size",
            "1",
            "--output",
            str(tmp_path / "debug"),
        ]
    )

    assert captured == [None]


def test_debug_preprocess_without_pages_passes_none_to_render(tmp_path, monkeypatch) -> None:
    captured: list[list[int] | None] = []
    preprocess_options: list[dict[str, object]] = []
    case = _case(tmp_path)
    _stub_review_command(monkeypatch, tmp_path, case)

    def fake_preprocess(before, after, **kwargs):
        preprocess_options.append(kwargs)
        return Path(after)

    monkeypatch.setattr(cli, "preprocess_image", fake_preprocess)
    monkeypatch.setattr(cli, "make_before_after_compare", lambda before, after, compare: Path(compare))

    def fake_render_pdf_pages(pdf_path, output_dir, *, dpi, page_numbers=None, max_pages=None):
        captured.append(page_numbers)
        return [SimpleNamespace(page_number=1, image_path=tmp_path / "page_001.png")]

    monkeypatch.setattr(cli, "render_pdf_pages", fake_render_pdf_pages)

    cli.main(
        [
            "debug-preprocess",
            "--input",
            str(tmp_path),
            "--limit",
            "1",
            "--review-sample-size",
            "1",
            "--output",
            str(tmp_path / "debug"),
        ]
    )

    assert captured == [None]
    assert preprocess_options[0]["deskew_mode"] == "off"
    assert preprocess_options[0]["remove_red_seal"] is True
    assert preprocess_options[0]["red_removal_mode"] == "neutralize"
    assert preprocess_options[0]["text_enhance_mode"] == "light"
    assert preprocess_options[0]["preprocess_profile"] == "conservative"


def test_full_document_helpers_disable_page_limit_and_marker() -> None:
    settings = SimpleNamespace(max_pages_before_marker=3, stop_marker="NỘI DUNG VỤ ÁN")

    assert cli._resolve_ocr_page_limit(SimpleNamespace(full_document=True, max_pages=20), settings) is None
    assert cli._resolve_stop_marker(SimpleNamespace(full_document=True), settings) == ""
    assert cli._resolve_ocr_page_limit(SimpleNamespace(full_document=False, max_pages=20), settings) == 20
    assert cli._resolve_ocr_page_limit(SimpleNamespace(full_document=False, max_pages=None), settings) == 3
    assert cli._resolve_stop_marker(SimpleNamespace(full_document=False), settings) == "NỘI DUNG VỤ ÁN"


def test_debug_ocr_review_full_document_passes_none_and_empty_marker(tmp_path, monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    case = _case(tmp_path)
    _stub_review_command(monkeypatch, tmp_path, case)
    monkeypatch.setattr(cli, "write_ocr_review", lambda output_path, records, *, base_dir: Path(output_path))
    monkeypatch.setattr(cli, "write_marker_report", lambda output_path, records: Path(output_path))
    monkeypatch.setattr(cli, "get_ocr_backend", lambda name, settings: _FakeOCRBackend(captured))

    cli.main(
        [
            "debug-ocr-review",
            "--input",
            str(tmp_path),
            "--limit",
            "1",
            "--review-sample-size",
            "1",
            "--ocr-backend",
            "surya",
            "--full-document",
            "--output",
            str(tmp_path / "debug"),
        ]
    )

    assert captured == [{"max_pages": None, "stop_marker": "", "debug_visual": True}]


def test_ocr_full_document_passes_none_and_empty_marker(tmp_path, monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    case = _case(tmp_path)
    monkeypatch.setattr(cli, "discover_pdfs", lambda input_dir, *, limit=None: [case.path])
    monkeypatch.setattr(cli, "case_files_for_paths", lambda paths: [case])
    monkeypatch.setattr(cli, "make_run_dir", lambda output: tmp_path / "ocr_debug")
    monkeypatch.setattr(cli, "get_ocr_backend", lambda name, settings: _FakeOCRBackend(captured))
    monkeypatch.setattr(cli, "_print_ocr_case_summary", lambda case_id, result, cache_dir, work_dir: None)

    cli.main(
        [
            "ocr",
            "--input-dir",
            str(tmp_path),
            "--limit",
            "1",
            "--cache-dir",
            str(tmp_path / "cache"),
            "--ocr-backend",
            "surya",
            "--full-document",
            "--debug-visual",
        ]
    )

    assert captured == [{"max_pages": None, "stop_marker": "", "debug_visual": True}]


def _case(tmp_path):
    return SimpleNamespace(
        case_id="case_001_synthetic",
        source_index=1,
        path=tmp_path / "synthetic.pdf",
        pdf_hash="synthetic",
    )


def _stub_review_command(monkeypatch, tmp_path, case) -> None:
    monkeypatch.setattr(cli, "make_run_dir", lambda output: tmp_path / "debug")
    monkeypatch.setattr(cli, "_sample_case_files", lambda args: [case])
    monkeypatch.setattr(cli, "write_image_grid", lambda output_path, *, title, cases, base_dir: Path(output_path))
    monkeypatch.setattr(cli, "write_preprocess_review", lambda output_path, *, cases, base_dir: Path(output_path))
    monkeypatch.setattr(cli, "write_run_index", lambda run_dir, links: Path(run_dir) / "index.html")
    monkeypatch.setattr(cli, "_maybe_open", lambda path, enabled: None)
    monkeypatch.setattr(cli, "_print_phase_result", lambda name, run_dir: None)


class _FakeOCRBackend:
    name = "surya"

    def __init__(self, captured: list[dict[str, object]]) -> None:
        self.captured = captured

    def check_available(self) -> OCRBackendStatus:
        return OCRBackendStatus("surya", True, "synthetic")

    def ocr_pdf_prefix(
        self,
        pdf_path,
        max_pages,
        stop_marker,
        debug_visual=False,
        work_dir=None,
    ) -> OCRResult:
        self.captured.append(
            {
                "max_pages": max_pages,
                "stop_marker": stop_marker,
                "debug_visual": debug_visual,
            }
        )
        return OCRResult(
            backend="surya",
            status="success",
            pages_processed=1,
            marker_found=False,
            marker_page=None,
            text="synthetic OCR",
        )
