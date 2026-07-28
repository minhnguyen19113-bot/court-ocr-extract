from __future__ import annotations

from fastapi import FastAPI

from court_ocr_extract.web_api.routes.forms import router as forms_router
from court_ocr_extract.web_api.routes.system import router as system_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Court OCR Extract Web API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )
    application.include_router(system_router, prefix="/api/v1")
    application.include_router(forms_router, prefix="/api/v1")
    return application


app = create_app()
