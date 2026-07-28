from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, Self

from court_ocr_extract.domain.audit import AuditEvent
from court_ocr_extract.domain.publishing import (
    PublishCandidate,
    PublishValidation,
    validate_publish_candidate,
)


class UnitOfWork(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool | None: ...

    def write_core(self, candidate: PublishCandidate) -> str: ...

    def append_audit(self, event: AuditEvent) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


@dataclass(frozen=True)
class PublishResult:
    published_record_id: str
    audit_event_id: str


class PublishRejected(ValueError):
    def __init__(self, validation: PublishValidation) -> None:
        self.validation = validation
        self.violation_codes = validation.violation_codes
        codes = ", ".join(code.value for code in self.violation_codes)
        super().__init__(f"Publish candidate rejected: {codes}")


class PublishService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def validate(self, candidate: PublishCandidate) -> PublishValidation:
        return validate_publish_candidate(candidate)

    def publish(self, candidate: PublishCandidate) -> PublishResult:
        validation = self.validate(candidate)
        if not validation.allowed:
            raise PublishRejected(validation)

        with self._unit_of_work_factory() as unit_of_work:
            try:
                published_record_id = unit_of_work.write_core(candidate)
                audit_event = AuditEvent(
                    event_type="CORE_PUBLISHED",
                    actor_id=candidate.approver_id or "",
                    subject_type="review_version",
                    subject_id=candidate.source_id,
                    metadata=(("schema_version", candidate.schema_version or ""),),
                )
                unit_of_work.append_audit(audit_event)
                unit_of_work.commit()
            except Exception:
                unit_of_work.rollback()
                raise

        return PublishResult(
            published_record_id=published_record_id,
            audit_event_id=audit_event.event_id,
        )
