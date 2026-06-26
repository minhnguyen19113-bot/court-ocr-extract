from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app_fastapi.routes.schemas import HealthResponse, JobRecord
from court_ocr_extract.config import get_settings
from court_ocr_extract.export.excel_writer import rows_from_result
from court_ocr_extract.file_utils import safe_stem, unique_path
from court_ocr_extract.models import model_to_dict
from court_ocr_extract.pipeline import process_pdf
from court_ocr_extract.privacy import redact_sensitive_payload


app = FastAPI(title="Vietnam Court OCR Extract API", version="0.3.0")
JOBS: dict[str, JobRecord] = {}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    mode = "remote-gpu-worker" if settings.use_remote_gpu_worker else "local-only"
    return HealthResponse(mode=mode)


@app.post("/api/process-pdf", response_model=JobRecord)
def process_pdf_upload(
    pdf: UploadFile = File(...),
    mode: str = Form("local-only"),
    max_pages_before_marker: int = Form(7),
    dpi: int = Form(300),
    remove_red_stamp: bool = Form(False),
    use_local_llm: bool = Form(True),
    use_mock_ocr: bool = Form(False),
    force: bool = Form(False),
) -> JobRecord:
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ nhận file PDF.")
    if max_pages_before_marker < 1 or max_pages_before_marker > 50:
        raise HTTPException(status_code=400, detail="max_pages_before_marker phải nằm trong khoảng 1..50.")

    settings = get_settings()
    settings.enable_mock_ocr = use_mock_ocr
    settings.processing_mode = mode
    settings.use_remote_gpu_worker = mode == "remote-gpu-worker"

    upload_dir = settings.raw_pdf_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = unique_path(upload_dir, f"{safe_stem(pdf.filename)}.pdf")
    with target.open("wb") as file_handle:
        shutil.copyfileobj(pdf.file, file_handle)

    job_id = uuid.uuid4().hex
    JOBS[job_id] = JobRecord(job_id=job_id, status="running")
    try:
        result = process_pdf(
            target,
            dpi=dpi,
            max_scan_pages=max_pages_before_marker,
            stop_on_marker=True,
            remove_red_stamp=remove_red_stamp,
            use_local_llm=use_local_llm,
            force=force,
            settings=settings,
        )
        payload: dict[str, Any] = redact_sensitive_payload(
            model_to_dict(result),
            include_sensitive=settings.persist_sensitive_json_text or settings.debug_sensitive,
        )
        payload["table_rows"] = rows_from_result(result.result)
        record = JobRecord(
            job_id=job_id,
            status="completed",
            result=payload,
            excel_download_url=_download_url("excel", result.excel_path),
            json_download_url=_download_url("json", result.extraction_json),
        )
    except Exception as exc:
        record = JobRecord(job_id=job_id, status="failed", error=str(exc))
    JOBS[job_id] = record
    return record


@app.get("/api/jobs/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> JobRecord:
    record = JOBS.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy job.")
    return record


@app.get("/api/download/{kind}/{filename}")
def download(kind: str, filename: str) -> FileResponse:
    settings = get_settings()
    directories = {"excel": settings.excel_dir, "json": settings.json_dir}
    directory = directories.get(kind)
    if directory is None:
        raise HTTPException(status_code=404, detail="Loại file không hợp lệ.")
    return _download_from(directory, filename)


def _download_url(kind: str, path: str | None) -> str | None:
    if not path:
        return None
    return f"/api/download/{kind}/{Path(path).name}"


def _download_from(directory: Path, filename: str) -> FileResponse:
    base = directory.resolve()
    path = (directory / Path(filename).name).resolve()
    if base not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy file.")
    return FileResponse(path)
