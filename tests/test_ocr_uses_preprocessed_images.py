from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

import court_ocr_extract.ocr_backends.surya_ocr as surya_module
from court_ocr_extract.ocr_backends.base import OCRBackendStatus
from court_ocr_extract.ocr_backends.surya_ocr import SuryaOCRBackend
from court_ocr_extract.settings import PipelineSettings


MODE_3 = {
    "deskew": "off",
    "red_seal_removal": True,
    "red_removal_mode": "inpaint",
    "text_enhance": "medium",
    "preprocess_profile": "balanced",
    "stamp_suppression": "balanced",
    "stamp_erase_mode": "component_white_fill",
    "ocr_stamp_filter": "balanced",
}


def test_surya_receives_final_preprocessed_image_and_writes_artifacts(tmp_path, monkeypatch) -> None:
    rendered = tmp_path / "rendered_original.png"
    Image.new("RGB", (240, 160), "white").save(rendered)
    work_dir = tmp_path / "case_synthetic"
    captured_images: list[Path] = []
    captured_options: list[dict[str, object]] = []
    backend = _backend(monkeypatch)
    monkeypatch.setattr(
        surya_module,
        "render_pdf_pages",
        lambda *args, **kwargs: [SimpleNamespace(image_path=rendered, page_number=1)],
    )

    def fake_preprocess(input_path, output_path, **kwargs):
        captured_options.append(kwargs)
        Image.new("L", (240, 160), 225).save(output_path)
        for key in (
            "intermediate_path",
            "red_mask_path",
            "black_text_protection_path",
            "text_enhanced_path",
        ):
            Image.new("L", (240, 160), 255).save(kwargs[key])
        kwargs["metadata"].update({"warnings": [], "synthetic": True})
        return Path(output_path)

    def fake_surya(image_paths):
        captured_images.extend(Path(path) for path in image_paths)
        return [{"blocks": [{"text": "synthetic", "bbox": [10, 10, 80, 30]}]}]

    monkeypatch.setattr(surya_module, "preprocess_image", fake_preprocess)
    monkeypatch.setattr(backend, "_run_surya_on_images", fake_surya)

    result = backend.ocr_pdf_prefix(
        tmp_path / "synthetic.pdf",
        max_pages=None,
        stop_marker="",
        debug_visual=True,
        work_dir=work_dir,
        preprocess_options=MODE_3,
    )

    preprocess_dir = work_dir / "preprocess"
    ocr_dir = work_dir / "ocr_surya"
    assert captured_images == [preprocess_dir / "page_001_ocr_input_stamp_suppressed.png"]
    assert captured_images[0] != rendered
    assert captured_options[0]["deskew_mode"] == "off"
    assert captured_options[0]["red_removal_mode"] == "inpaint"
    assert captured_options[0]["text_enhance_mode"] == "medium"
    assert captured_options[0]["preprocess_profile"] == "balanced"
    assert result.metadata["ocr_input_source"] == "preprocessed"
    assert result.metadata["stamp_suppression"] == "balanced"
    assert result.metadata["stamp_erase_mode"] == "component_white_fill"
    assert result.metadata["ocr_stamp_filter"] == "balanced"
    assert result.metadata["raw_line_count"] == 1
    assert result.metadata["filtered_line_count"] == 1
    assert result.metadata["excluded_stamp_line_count"] == 0
    assert (preprocess_dir / "page_001_original.png").exists()
    assert (preprocess_dir / "page_001_red_mask.png").exists()
    assert (preprocess_dir / "page_001_black_text_protection_mask.png").exists()
    assert (preprocess_dir / "page_001_seal_removed.png").exists()
    assert (preprocess_dir / "page_001_text_enhanced.png").exists()
    assert (preprocess_dir / "page_001_final_preprocessed.png").exists()
    assert (preprocess_dir / "page_001_stamp_suppression_mask.png").exists()
    assert (preprocess_dir / "page_001_stamp_object_mask.png").exists()
    assert (preprocess_dir / "page_001_stamp_object_erased.png").exists()
    assert (preprocess_dir / "page_001_ocr_input_stamp_suppressed.png").exists()
    assert (preprocess_dir / "page_001_metadata.json").exists()
    assert (ocr_dir / "page_001_ocr_input.png").exists()
    manifest = json.loads((ocr_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["metadata"]["ocr_input_source"] == "preprocessed"
    assert manifest["metadata"]["text_enhance"] == "medium"
    assert manifest["pages"][0]["artifacts"]["ocr_input_source"] == "preprocessed"


def test_surya_without_preprocess_uses_rendered_original(tmp_path, monkeypatch) -> None:
    rendered = tmp_path / "rendered_original.png"
    Image.new("RGB", (180, 120), "white").save(rendered)
    backend = _backend(monkeypatch)
    captured: list[Path] = []
    monkeypatch.setattr(
        surya_module,
        "render_pdf_pages",
        lambda *args, **kwargs: [SimpleNamespace(image_path=rendered, page_number=1)],
    )
    monkeypatch.setattr(
        surya_module,
        "preprocess_image",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("preprocess must stay off")),
    )

    def fake_surya(image_paths):
        captured.extend(Path(path) for path in image_paths)
        return [{"blocks": [{"text": "synthetic", "bbox": [5, 5, 50, 20]}]}]

    monkeypatch.setattr(backend, "_run_surya_on_images", fake_surya)
    result = backend.ocr_pdf_prefix(
        tmp_path / "synthetic.pdf",
        max_pages=1,
        stop_marker="",
        work_dir=tmp_path / "rendered_case",
    )

    assert captured == [rendered]
    assert result.metadata["ocr_input_source"] == "rendered_original"
    assert result.metadata["raw_line_count"] == 1
    assert result.metadata["filtered_line_count"] == 1
    assert result.metadata["excluded_stamp_line_count"] == 0
    assert result.metadata["ocr_review_needed"] is False


def test_preprocess_failure_still_uses_named_final_safe_copy(tmp_path, monkeypatch) -> None:
    rendered = tmp_path / "rendered_original.png"
    Image.new("RGB", (180, 120), "white").save(rendered)
    backend = _backend(monkeypatch)
    captured: list[Path] = []
    monkeypatch.setattr(
        surya_module,
        "render_pdf_pages",
        lambda *args, **kwargs: [SimpleNamespace(image_path=rendered, page_number=1)],
    )
    monkeypatch.setattr(surya_module, "preprocess_image", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError()))
    monkeypatch.setattr(
        backend,
        "_run_surya_on_images",
        lambda image_paths: captured.extend(Path(path) for path in image_paths)
        or [{"blocks": [{"text": "synthetic", "bbox": [5, 5, 50, 20]}]}],
    )

    result = backend.ocr_pdf_prefix(
        tmp_path / "synthetic.pdf",
        max_pages=1,
        stop_marker="",
        work_dir=tmp_path / "fallback_case",
        preprocess_options=MODE_3,
    )

    assert captured[0].name == "page_001_ocr_input_stamp_suppressed.png"
    assert captured[0].exists()
    assert (captured[0].parent / "page_001_final_preprocessed.png").exists()
    assert any("preprocess_failed_using_rendered_safe_copy" in warning for warning in result.warnings)


def _backend(monkeypatch) -> SuryaOCRBackend:
    backend = SuryaOCRBackend(PipelineSettings())
    monkeypatch.setattr(
        backend,
        "check_available",
        lambda: OCRBackendStatus("surya", True, "synthetic available"),
    )
    return backend
