from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from court_ocr_extract import cli
from court_ocr_extract.ocr_backends.base import OCRBackendStatus, OCRResult


MODE_3_ARGS = [
    "--use-preprocessed",
    "--deskew",
    "off",
    "--red-seal-removal",
    "on",
    "--red-removal-mode",
    "inpaint",
    "--text-enhance",
    "medium",
    "--preprocess-profile",
    "balanced",
    "--stamp-suppression",
    "balanced",
    "--ocr-stamp-filter",
    "balanced",
]


def test_debug_ocr_review_passes_mode3_preprocess_options(tmp_path, monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    backend = _FakeBackend(captured)
    _stub_common(monkeypatch, tmp_path, backend)
    monkeypatch.setattr(cli, "_sample_case_files", lambda args: [_case(tmp_path)])
    monkeypatch.setattr(cli, "write_ocr_review", lambda output_path, records, *, base_dir: Path(output_path))
    monkeypatch.setattr(cli, "write_marker_report", lambda output_path, records: Path(output_path))

    cli.main(
        [
            "debug-ocr-review",
            "--input",
            str(tmp_path),
            "--review-sample-size",
            "1",
            "--ocr-backend",
            "surya",
            "--full-document",
            "--output",
            str(tmp_path / "debug"),
            *MODE_3_ARGS,
        ]
    )

    assert captured[0]["max_pages"] is None
    assert captured[0]["stop_marker"] == ""
    assert captured[0]["preprocess_options"] == {
        "deskew": "off",
        "red_seal_removal": True,
        "red_removal_mode": "inpaint",
        "text_enhance": "medium",
        "preprocess_profile": "balanced",
        "stamp_suppression": "balanced",
        "ocr_stamp_filter": "balanced",
    }


def test_ocr_cache_records_preprocessed_input_metadata(tmp_path, monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    backend = _FakeBackend(captured)
    case = _case(tmp_path)
    _stub_common(monkeypatch, tmp_path, backend)
    monkeypatch.setattr(cli, "discover_pdfs", lambda input_dir, *, limit=None: [case.path])
    monkeypatch.setattr(cli, "case_files_for_paths", lambda paths: [case])
    monkeypatch.setattr(cli, "_print_ocr_case_summary", lambda *args: None)
    cache_dir = tmp_path / "cache"

    cli.main(
        [
            "ocr",
            "--input-dir",
            str(tmp_path),
            "--cache-dir",
            str(cache_dir),
            "--ocr-backend",
            "surya",
            "--full-document",
            "--debug-visual",
            *MODE_3_ARGS,
        ]
    )

    payload = json.loads((cache_dir / "case_001_synthetic.json").read_text(encoding="utf-8"))
    assert payload["result"]["metadata"]["ocr_input_source"] == "preprocessed"
    assert payload["result"]["metadata"]["red_removal_mode"] == "inpaint"
    assert payload["result"]["metadata"]["text_enhance"] == "medium"


def _stub_common(monkeypatch, tmp_path, backend) -> None:
    monkeypatch.setattr(cli, "get_ocr_backend", lambda name, settings: backend)
    monkeypatch.setattr(cli, "make_run_dir", lambda output: tmp_path / "debug")
    monkeypatch.setattr(cli, "write_run_index", lambda run_dir, links: Path(run_dir) / "index.html")
    monkeypatch.setattr(cli, "_maybe_open", lambda path, enabled: None)
    monkeypatch.setattr(cli, "_print_phase_result", lambda name, run_dir: None)


def _case(tmp_path):
    return SimpleNamespace(
        case_id="case_001_synthetic",
        source_index=1,
        path=tmp_path / "synthetic.pdf",
        pdf_hash="synthetic",
    )


class _FakeBackend:
    name = "surya"

    def __init__(self, captured):
        self.captured = captured

    def check_available(self):
        return OCRBackendStatus("surya", True, "synthetic")

    def ocr_pdf_prefix(self, pdf_path, max_pages, stop_marker, debug_visual=False, work_dir=None, preprocess_options=None):
        self.captured.append(
            {
                "max_pages": max_pages,
                "stop_marker": stop_marker,
                "debug_visual": debug_visual,
                "preprocess_options": preprocess_options,
            }
        )
        metadata = {"ocr_input_source": "rendered_original"}
        if preprocess_options is not None:
            metadata = {"ocr_input_source": "preprocessed", **preprocess_options}
        return OCRResult(
            backend="surya",
            status="success",
            pages_processed=1,
            marker_found=False,
            marker_page=None,
            text="synthetic",
            metadata=metadata,
        )
