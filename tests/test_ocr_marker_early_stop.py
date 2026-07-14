from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from court_ocr_extract.ocr_backends.base import OCRBackendStatus
from court_ocr_extract.ocr_backends.surya_ocr import SuryaOCRBackend
from court_ocr_extract.settings import DEFAULT_STOP_MARKER, PipelineSettings


def _backend(monkeypatch) -> SuryaOCRBackend:
    backend = SuryaOCRBackend(PipelineSettings())
    monkeypatch.setattr(
        backend,
        "check_available",
        lambda: OCRBackendStatus("surya", True, "synthetic"),
    )
    return backend


def _patch_pages(monkeypatch, tmp_path, backend, *, pages_total: int, marker_page: int | None):
    import court_ocr_extract.ocr_backends.surya_ocr as module

    calls: list[int] = []
    initializations: list[int] = []
    monkeypatch.setattr(module, "get_pdf_page_count", lambda path: pages_total)

    def render(pdf_path, output_dir, *, dpi, page_numbers):
        rendered = []
        for page_number in page_numbers:
            path = tmp_path / f"page_{page_number:03d}.png"
            Image.new("RGB", (120, 80), "white").save(path)
            rendered.append(SimpleNamespace(page_number=page_number, image_path=path))
        return rendered

    def create_runner(**kwargs):
        initializations.append(1)

        def run(paths: list[Path]):
            predictions = []
            for path in paths:
                page_number = int(path.stem.rsplit("_", 1)[-1])
                calls.append(page_number)
                text = "synthetic pre-content"
                if page_number == marker_page:
                    text = "synthetic pre-content\nNỘI DUNG VỤ ÁN\nsynthetic body"
                predictions.append({"text_lines": [{"text": line} for line in text.splitlines()]})
            return predictions

        return run

    monkeypatch.setattr(module, "render_pdf_pages", render)
    monkeypatch.setattr(backend, "_create_surya_page_runner", create_runner)
    return calls, initializations


def test_early_stop_calls_only_through_marker_page_and_reuses_runner(tmp_path, monkeypatch) -> None:
    backend = _backend(monkeypatch)
    calls, initializations = _patch_pages(
        monkeypatch, tmp_path, backend, pages_total=10, marker_page=3
    )

    result = backend.ocr_pdf_prefix(
        tmp_path / "synthetic.pdf",
        max_pages=None,
        stop_marker=DEFAULT_STOP_MARKER,
        work_dir=tmp_path / "run",
    )

    assert calls == [1, 2, 3]
    assert len(initializations) == 1
    assert result.marker_found is True
    assert result.marker_page == 3
    assert result.pages_processed == 3
    assert result.metadata["early_stop"]["pages_skipped_after_marker"] == 7
    assert result.metadata["early_stop"]["page_batch_size"] == 1
    assert "NỘI DUNG VỤ ÁN" not in result.text
    assert "synthetic body" not in result.text


def test_marker_not_found_processes_all_pages_and_warns(tmp_path, monkeypatch) -> None:
    backend = _backend(monkeypatch)
    calls, _ = _patch_pages(monkeypatch, tmp_path, backend, pages_total=4, marker_page=None)

    result = backend.ocr_pdf_prefix(
        tmp_path / "synthetic.pdf",
        max_pages=None,
        stop_marker=DEFAULT_STOP_MARKER,
        work_dir=tmp_path / "run_missing",
    )

    assert calls == [1, 2, 3, 4]
    assert result.status == "success"
    assert result.marker_found is False
    assert result.metadata["early_stop"]["reason"] == "marker_not_found"
    assert any("Marker not found" in warning for warning in result.warnings)


def test_full_document_override_uses_bulk_path_and_keeps_marker_body(tmp_path, monkeypatch) -> None:
    import court_ocr_extract.ocr_backends.surya_ocr as module

    backend = _backend(monkeypatch)
    image_paths = []
    for page_number in range(1, 5):
        path = tmp_path / f"full_{page_number:03d}.png"
        Image.new("RGB", (120, 80), "white").save(path)
        image_paths.append(path)
    monkeypatch.setattr(
        module,
        "render_pdf_pages",
        lambda *args, **kwargs: [
            SimpleNamespace(page_number=index, image_path=path)
            for index, path in enumerate(image_paths, start=1)
        ],
    )
    monkeypatch.setattr(
        backend,
        "_run_surya_on_images",
        lambda paths: [
            {"text_lines": [{"text": "NỘI DUNG VỤ ÁN" if index == 3 else "synthetic"}]}
            for index, _ in enumerate(paths, start=1)
        ],
    )

    result = backend.ocr_pdf_prefix(
        tmp_path / "synthetic.pdf",
        max_pages=None,
        stop_marker="",
        work_dir=tmp_path / "run_full",
    )

    assert result.pages_processed == 4
    assert result.marker_found is False
    assert result.metadata["early_stop"]["enabled"] is False
    assert result.metadata["early_stop"]["reason"] == "full_document_override"
    assert "NỘI DUNG VỤ ÁN" in result.text
