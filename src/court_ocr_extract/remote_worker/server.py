from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile

from court_ocr_extract.config import get_settings
from court_ocr_extract.extraction.local_llm_extractor import LocalLLMExtractor
from court_ocr_extract.models import model_to_dict
from court_ocr_extract.ocr.mock_adapter import MockOcrAdapter
from court_ocr_extract.ocr.surya_adapter import SuryaOcrEngine
from court_ocr_extract.remote_worker.cleanup import cleanup_worker_temp, ensure_worker_temp_dir
from court_ocr_extract.remote_worker.schemas import (
    CleanupResponse,
    ExtractRequest,
    JobStatusResponse,
    WorkerStatus,
)


app = FastAPI(title="Court OCR Remote GPU Worker", version="0.1.0")


def _authorize(authorization: str | None = Header(default=None)) -> None:
    token = get_settings().gpu_worker_token
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Invalid GPU worker token.")


@app.get("/health", response_model=WorkerStatus)
def health(_: None = Depends(_authorize)) -> WorkerStatus:
    settings = get_settings()
    mode = "mock" if settings.enable_mock_ocr else "surya"
    return WorkerStatus(ok=True, mode=mode)


@app.post("/ocr-page")
def ocr_page(
    page_number: int = Form(...),
    image: UploadFile = File(...),
    _: None = Depends(_authorize),
):
    settings = get_settings()
    temp_dir = ensure_worker_temp_dir()
    target = temp_dir / Path(image.filename or f"page_{page_number}.png").name
    with target.open("wb") as file_handle:
        shutil.copyfileobj(image.file, file_handle)
    try:
        engine = MockOcrAdapter() if settings.enable_mock_ocr else SuryaOcrEngine(settings.surya_language_list)
        page = engine.ocr_page(target, page_number=page_number)
        return {"page": model_to_dict(page)}
    finally:
        target.unlink(missing_ok=True)


@app.post("/extract")
def extract(payload: ExtractRequest, _: None = Depends(_authorize)):
    settings = get_settings()
    output = LocalLLMExtractor(settings).extract(payload.text)
    return model_to_dict(output)


@app.post("/cleanup", response_model=CleanupResponse)
def cleanup(_: None = Depends(_authorize)) -> CleanupResponse:
    removed = cleanup_worker_temp()
    return CleanupResponse(ok=True, removed_files=removed)


@app.get("/job-status", response_model=JobStatusResponse)
def job_status(job_id: str | None = None, _: None = Depends(_authorize)) -> JobStatusResponse:
    return JobStatusResponse(job_id=job_id)
