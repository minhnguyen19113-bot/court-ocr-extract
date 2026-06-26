from __future__ import annotations

import io
import zipfile
from pathlib import Path

from court_ocr_extract.pipeline import batch_pipeline
from scripts import transfer_server


class _Settings:
    def __init__(self, root: Path) -> None:
        self.checkpoint_dir = root / "checkpoints"
        self.json_dir = root / "json"
        self.excel_dir = root / "excel"
        self.persist_sensitive_json_text = False
        self.debug_sensitive = False
        for directory in [self.checkpoint_dir, self.json_dir, self.excel_dir]:
            directory.mkdir(parents=True, exist_ok=True)


def test_process_batch_limit_uses_first_sorted_pdfs(tmp_path, monkeypatch):
    input_dir = tmp_path / "uploads"
    input_dir.mkdir()
    for index in range(12):
        (input_dir / f"{index:02d}.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

    seen: list[str] = []

    def fake_process_pdf(pdf_path, **_kwargs):
        seen.append(Path(pdf_path).name)
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(batch_pipeline, "process_pdf", fake_process_pdf)

    summary = batch_pipeline.process_batch(
        input_dir,
        limit=10,
        settings=_Settings(tmp_path / "out"),
    )

    assert summary["total"] == 10
    assert summary["failed"] == 10
    assert seen == [f"{index:02d}.pdf" for index in range(10)]


def test_transfer_zip_extracts_only_pdfs_with_generated_names(tmp_path):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("private-name.pdf", b"%PDF-1.4\n%%EOF\n")
        archive.writestr("notes.txt", "not a pdf")

    saved = transfer_server._extract_pdf_zip(payload.getvalue(), tmp_path)

    assert len(saved) == 1
    assert saved[0].startswith("uploaded_")
    assert saved[0].endswith(".pdf")
    assert (tmp_path / saved[0]).read_bytes().startswith(b"%PDF")
