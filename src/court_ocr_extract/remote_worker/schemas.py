from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1)


class WorkerStatus(BaseModel):
    ok: bool
    mode: str
    detail: str | None = None


class CleanupResponse(BaseModel):
    ok: bool
    removed_files: int = 0
    detail: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str | None = None
    status: str = "not_implemented"
    detail: str = "This worker processes synchronous requests by default."
    metadata: dict[str, Any] = Field(default_factory=dict)
