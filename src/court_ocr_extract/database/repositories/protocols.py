from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


class JobRepository(Protocol):
    def get(self, job_id: UUID) -> Any | None: ...

    def add(self, job: Any) -> None: ...

    def set_status(self, job_id: UUID, status: str) -> None: ...


class ReviewRepository(Protocol):
    def get_version(self, review_version_id: UUID) -> Any | None: ...

    def add_version(self, review_version: Any) -> None: ...

    def get_approval(self, review_version_id: UUID) -> Any | None: ...


class PublishedSnapshotRepository(Protocol):
    def get(self, published_snapshot_id: UUID) -> Any | None: ...

    def add(self, published_snapshot: Any) -> None: ...


class FormRepository(Protocol):
    def get_definition(self, form_definition_id: UUID) -> Any | None: ...

    def add_generation_request(self, request: Any) -> None: ...

    def add_generated_document(self, generated_document: Any) -> None: ...


class AuditEventRepository(Protocol):
    """The audit boundary deliberately exposes no mutation or deletion."""

    def append(self, event: Any) -> None: ...

    def list(
        self,
        *,
        subject_type: str | None = None,
        subject_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> Sequence[Any]: ...
