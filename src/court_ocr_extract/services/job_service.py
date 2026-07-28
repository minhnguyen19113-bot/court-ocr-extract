from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from court_ocr_extract.domain.workflow import WorkflowState


@dataclass(frozen=True)
class JobDescriptor:
    job_id: str
    request_key: str
    state: WorkflowState = WorkflowState.DRAFT


class JobRepository(Protocol):
    def add(self, descriptor: JobDescriptor) -> None: ...


class JobService:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def register_draft(self, *, job_id: str, request_key: str) -> JobDescriptor:
        descriptor = JobDescriptor(job_id=job_id, request_key=request_key)
        self._repository.add(descriptor)
        return descriptor
