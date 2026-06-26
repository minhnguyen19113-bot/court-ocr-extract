from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JobRecord(BaseModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    excel_download_url: str | None = None
    json_download_url: str | None = None


class HealthResponse(BaseModel):
    ok: bool = True
    app: str = "court-ocr-extract"
    mode: str = Field(default="local-only")
