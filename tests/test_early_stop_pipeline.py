from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from court_ocr_extract.ocr.mock_adapter import MockOcrAdapter
from court_ocr_extract.pipeline import early_stop_pipeline as module
from court_ocr_extract.pipeline.early_stop_pipeline import EarlyStopConfig, EarlyStopPipeline


def test_early_stop_stops_at_content_marker(tmp_path, monkeypatch):
    settings = SimpleNamespace(
        images_dir=tmp_path / "images",
        processed_images_dir=tmp_path / "processed",
        processed_intermediate_dir=tmp_path / "intermediate",
        ocr_raw_dir=tmp_path / "ocr_raw",
        section_marker="NỘI DUNG VỤ ÁN",
    )

    def fake_render_pdf_page(pdf_path: Path, page_number: int, output_dir: Path, dpi: int):
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / f"page_{page_number}.png"
        Image.new("RGB", (120, 80), "white").save(image_path)
        return SimpleNamespace(page_number=page_number, image_path=image_path, width=120, height=80)

    def fake_preprocess(input_path: Path, output_path: Path, **kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        Image.open(input_path).save(output_path)
        return output_path

    monkeypatch.setattr(module, "render_pdf_page", fake_render_pdf_page)
    monkeypatch.setattr(module, "preprocess_for_ocr", fake_preprocess)

    adapter = MockOcrAdapter(
        page_texts={
            1: "Bị cáo: Người Tham Gia A",
            2: "NỘI DUNG VỤ ÁN\nPhần không dùng",
            3: "Không được OCR",
        }
    )
    document = EarlyStopPipeline(settings, adapter).run(
        pdf_path=tmp_path / "fake.pdf",
        output_stem="fake",
        page_count=10,
        config=EarlyStopConfig(
            dpi=300,
            remove_red_stamp=True,
            max_pages_before_marker=5,
            stop_on_marker=True,
            force_full_ocr=False,
        ),
    )

    assert document.marker_found is True
    assert document.marker_page == 2
    assert document.pages_ocr == 2
    assert document.stop_reason == "content_marker_found"
    assert "Phần không dùng" not in document.text
