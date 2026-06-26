from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from court_ocr_extract.config import get_settings
from court_ocr_extract.export.excel_writer import rows_from_result
from court_ocr_extract.file_utils import safe_stem, unique_path
from court_ocr_extract.models import model_to_dict
from court_ocr_extract.overlay import draw_bbox_overlay
from court_ocr_extract.pipeline import process_pdf


app = FastAPI(title="Vietnam Court OCR Extract", version="0.2.0")
templates = Jinja2Templates(directory=str(ROOT / "templates"))
LOGGER = logging.getLogger(__name__)


@app.get("/", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse(request, "upload.html")


@app.post("/api/process")
def process_upload(
    pdf: UploadFile = File(...),
    max_scan_pages: int = Form(7),
    dpi: int = Form(300),
    stop_on_marker: bool = Form(True),
    remove_red_stamp: bool = Form(False),
    use_local_llm: bool = Form(False),
    use_mock_ocr: bool = Form(False),
    force: bool = Form(False),
    debug_bbox: bool = Form(False),
):
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chi nhan file PDF.")
    if dpi not in {200, 300, 400, 500}:
        raise HTTPException(status_code=400, detail="DPI hop le: 200, 300, 400, 500.")
    if max_scan_pages < 1 or max_scan_pages > 30:
        raise HTTPException(status_code=400, detail="max_scan_pages phai nam trong khoang 1..30.")

    settings = get_settings()
    LOGGER.info(
        "Processing upload flags: local_llm=%s max_scan_pages=%s dpi=%s remove_red_stamp=%s debug_bbox=%s",
        use_local_llm,
        max_scan_pages,
        dpi,
        remove_red_stamp,
        debug_bbox,
    )
    upload_dir = settings.raw_pdf_dir / "uploads"
    if use_mock_ocr:
        settings.enable_mock_ocr = True
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = unique_path(upload_dir, f"{safe_stem(pdf.filename)}.pdf")
    with target.open("wb") as file_handle:
        shutil.copyfileobj(pdf.file, file_handle)

    try:
        result = process_pdf(
            target,
            dpi=dpi,
            max_scan_pages=max_scan_pages,
            stop_on_marker=stop_on_marker,
            remove_red_stamp=remove_red_stamp,
            use_local_llm=use_local_llm,
            force=force,
            settings=settings,
        )
    except Exception as exc:
        detail = _friendly_error_detail(exc)
        raise HTTPException(status_code=500, detail=detail) from exc

    bbox_urls = []
    if debug_bbox:
        bbox_urls = _write_bbox_debug_images(result)
        result.bbox_debug_images = bbox_urls

    payload = model_to_dict(result)
    payload["table_rows"] = rows_from_result(result.result)
    payload["excel_download_url"] = (
        f"/download/excel/{Path(result.excel_path).name}" if result.excel_path else None
    )
    payload["json_download_url"] = (
        f"/download/json/{Path(result.extraction_json).name}" if result.extraction_json else None
    )
    payload["bbox_debug_urls"] = [f"/download/bbox/{Path(path).name}" for path in bbox_urls]
    return payload


@app.get("/download/excel/{filename}")
def download_excel(filename: str):
    return _download_from(get_settings().excel_dir, filename)


@app.get("/download/json/{filename}")
def download_json(filename: str):
    return _download_from(get_settings().json_dir, filename)


@app.get("/download/bbox/{filename}")
def download_bbox(filename: str):
    return _download_from(get_settings().bbox_debug_dir, filename)


def _download_from(directory: Path, filename: str) -> FileResponse:
    path = (directory / Path(filename).name).resolve()
    if directory.resolve() not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Khong tim thay file.")
    return FileResponse(path)


def _write_bbox_debug_images(result) -> list[str]:
    settings = get_settings()
    images = []
    pages = result.result.metadata.get("ocr_pages", [])
    stem = safe_stem(result.result.source_file or "upload")
    for page in pages:
        image_path = page.get("processed_image_path")
        if not image_path:
            continue
        from court_ocr_extract.models import OcrPage

        page_model = OcrPage(**page)
        output_path = settings.bbox_debug_dir / f"{stem}_page_{page_model.page_number:03d}_overlay.png"
        try:
            draw_bbox_overlay(image_path, page_model, output_path)
        except Exception:
            continue
        images.append(str(output_path))
    return images


def _friendly_error_detail(exc: Exception) -> str:
    detail = str(exc)
    if "docker binary not found" in detail or "Install Docker" in detail:
        return (
            "Surya OCR 0.20 dang tu dong chon backend vLLM va co gang spawn Docker, "
            "nhung moi truong hien tai khong co Docker binary. "
            "Tren Vast.ai, cach de nhat la dung GPU 24GB (RTX 3090/4090), chay vLLM server rieng, "
            "roi set SURYA_INFERENCE_URL de Surya attach vao server do thay vi tu spawn Docker. "
            "Neu chi muon test giao dien/pipeline, tick 'Mock OCR'. "
            f"Chi tiet ky thuat: {exc}"
        )
    if "llama-server" in detail or "LLAMA_CPP" in detail or "llama.cpp" in detail:
        return (
            "Surya OCR 0.20 dang dung backend llama.cpp tren may nay nhung chua thay llama-server. "
            "De OCR that, hay cai/chay llama-server hoac chay tren GPU/Vast.ai voi vLLM. "
            "Neu chi muon test giao dien/pipeline, tick 'Mock OCR'. "
            f"Chi tiet ky thuat: {exc}"
        )
    return detail
