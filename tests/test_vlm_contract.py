from __future__ import annotations

import json

from PIL import Image

from court_ocr_extract.vlm_backends.fake_vlm import FakeVLMBackend
from court_ocr_extract.vlm_page_reader import read_images_with_vlm, safe_vlm_backend_name
from scripts.smoke_vlm_synthetic import run_smoke


def test_fake_vlm_backend_returns_page_result(tmp_path):
    image_path = tmp_path / "page.png"
    Image.new("RGB", (240, 320), "white").save(image_path)

    result = FakeVLMBackend().read_page(image_path, "Read page {page_number}", 1)

    assert result.page_index == 1
    assert "# PAGE 1" in result.text
    assert result.unreadable_count == 0
    assert result.timing["total_seconds"] >= 0


def test_vlm_page_result_bridges_to_ocr_result(tmp_path):
    image_path = tmp_path / "page.png"
    Image.new("RGB", (240, 320), "white").save(image_path)

    record = read_images_with_vlm(
        [image_path],
        case_id="case_001_contract",
        source_index=1,
        pdf_hash="synthetic",
        output_dir=tmp_path / "vlm",
        backend=FakeVLMBackend(),
    )

    assert record.result.backend == "vlm_fake_fake_vlm_contract"
    assert ":" not in record.result.backend
    assert record.result.pages_processed == 1
    assert record.result.text
    assert record.result.pages[0].image_path == str(image_path)
    assert record.result.pages[0].text
    assert (tmp_path / "vlm" / "page_001.md").exists()
    assert (tmp_path / "vlm" / "combined_vlm_text.md").exists()


def test_safe_vlm_backend_name_removes_path_unsafe_chars():
    assert safe_vlm_backend_name("ollama", "qwen2.5vl:3b") == "vlm_ollama_qwen2_5vl_3b"


def test_vlm_synthetic_smoke_creates_safe_manifest(tmp_path):
    result = run_smoke(
        output_root=tmp_path / "outputs",
        synthetic_root=tmp_path / "synthetic",
    )

    manifest_path = tmp_path / "outputs" / "debug_visual" / "vlm_synthetic_smoke" / "manifest.json"
    page_markdown = tmp_path / "outputs" / "debug_visual" / "vlm_synthetic_smoke" / "page_001.md"
    combined_text = tmp_path / "outputs" / "debug_visual" / "vlm_synthetic_smoke" / "combined_vlm_text.md"
    debug_html = tmp_path / "outputs" / "debug_visual" / "vlm_synthetic_smoke" / "index.html"

    assert result["manifest_path"] == str(manifest_path)
    assert page_markdown.exists()
    assert combined_text.exists()
    assert debug_html.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["real_data_accessed"] is False
    assert manifest["provider"] == "fake"
    assert manifest["failed_steps"] == []
    assert "data/raw_pdfs" not in json.dumps(manifest)
    assert "data\\raw_pdfs" not in json.dumps(manifest)

