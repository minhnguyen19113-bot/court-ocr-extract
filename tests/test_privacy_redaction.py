from types import SimpleNamespace

from court_ocr_extract.pipeline.single_file_pipeline import process_ocr_text
from court_ocr_extract.privacy import redact_sensitive_payload


def test_redact_sensitive_payload_removes_full_ocr_text():
    payload = {
        "result": {
            "text_before_marker": "Synthetic OCR header",
            "corrected_text": "Synthetic full OCR",
            "metadata": {"ocr_pages": [{"text": "Synthetic page text"}]},
        }
    }

    redacted = redact_sensitive_payload(payload)

    assert redacted["result"]["text_before_marker"] is None
    assert redacted["result"]["corrected_text"] is None
    assert "ocr_pages" not in redacted["result"]["metadata"]
    assert redacted["result"]["metadata"]["ocr_pages_redacted"] is True


def test_process_ocr_text_does_not_persist_full_text_by_default(tmp_path):
    settings = SimpleNamespace(
        ensure_dirs=lambda: None,
        enable_local_llm=False,
        enable_gliner=False,
        extract_without_marker=True,
        section_marker="NỘI DUNG VỤ ÁN",
        max_scan_pages=7,
        persist_ocr_text_artifacts=False,
        persist_sensitive_json_text=False,
        debug_sensitive=False,
        ocr_corrected_dir=tmp_path / "ocr_corrected",
        json_dir=tmp_path / "json",
        excel_dir=tmp_path / "excel",
    )

    result = process_ocr_text(
        "Bị cáo: Người Tham Gia A\nNỘI DUNG VỤ ÁN\nPhần sau marker",
        output_stem="synthetic",
        settings=settings,
        use_local_llm=False,
    )

    assert result.corrected_text_path is None
    assert result.text_before_marker_path is None
    assert result.result.text_before_marker == "Bị cáo: Người Tham Gia A"
    assert '"text_before_marker": null' in (tmp_path / "json" / "synthetic.json").read_text(
        encoding="utf-8"
    )
