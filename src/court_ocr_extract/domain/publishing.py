from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from court_ocr_extract.domain.field_status import (
    FieldMissingReason,
    FieldValueStatus,
    is_publishable_field_status,
)
from court_ocr_extract.domain.workflow import WorkflowState


class PublishSourceKind(str, Enum):
    MACHINE_EXTRACTION = "MACHINE_EXTRACTION"
    REVIEW_VERSION = "REVIEW_VERSION"


class PublishViolationCode(str, Enum):
    MACHINE_EXTRACTION_NOT_PUBLISHABLE = "MACHINE_EXTRACTION_NOT_PUBLISHABLE"
    STATE_NOT_APPROVED = "STATE_NOT_APPROVED"
    APPROVAL_MISSING = "APPROVAL_MISSING"
    APPROVER_MISSING = "APPROVER_MISSING"
    CRITICAL_WARNINGS_UNRESOLVED = "CRITICAL_WARNINGS_UNRESOLVED"
    REQUIRED_FIELD_NOT_PUBLISHABLE = "REQUIRED_FIELD_NOT_PUBLISHABLE"
    REQUIRED_FIELD_MISSING_REASON = "REQUIRED_FIELD_MISSING_REASON"
    SNAPSHOT_NOT_LOCKED = "SNAPSHOT_NOT_LOCKED"
    SCHEMA_VERSION_MISSING = "SCHEMA_VERSION_MISSING"
    ALREADY_PUBLISHED = "ALREADY_PUBLISHED"


@dataclass(frozen=True)
class PublishField:
    field_key: str
    status: FieldValueStatus
    required: bool = False
    missing_reason: FieldMissingReason | None = None


@dataclass(frozen=True)
class PublishCandidate:
    source_kind: PublishSourceKind
    source_id: str
    state: WorkflowState
    fields: tuple[PublishField, ...] = ()
    approval_id: str | None = None
    approver_id: str | None = None
    critical_warning_count: int = 0
    is_locked: bool = False
    schema_version: str | None = None
    is_published: bool = False


@dataclass(frozen=True)
class PublishValidation:
    violation_codes: tuple[PublishViolationCode, ...]

    @property
    def allowed(self) -> bool:
        return not self.violation_codes


def validate_publish_candidate(candidate: PublishCandidate) -> PublishValidation:
    violations: list[PublishViolationCode] = []

    if candidate.source_kind is not PublishSourceKind.REVIEW_VERSION:
        violations.append(PublishViolationCode.MACHINE_EXTRACTION_NOT_PUBLISHABLE)
    if candidate.state is not WorkflowState.APPROVED:
        violations.append(PublishViolationCode.STATE_NOT_APPROVED)
    if not candidate.approval_id:
        violations.append(PublishViolationCode.APPROVAL_MISSING)
    if not candidate.approver_id:
        violations.append(PublishViolationCode.APPROVER_MISSING)
    if candidate.critical_warning_count:
        violations.append(PublishViolationCode.CRITICAL_WARNINGS_UNRESOLVED)
    if not candidate.is_locked:
        violations.append(PublishViolationCode.SNAPSHOT_NOT_LOCKED)
    if not candidate.schema_version:
        violations.append(PublishViolationCode.SCHEMA_VERSION_MISSING)
    if candidate.is_published:
        violations.append(PublishViolationCode.ALREADY_PUBLISHED)

    for field in candidate.fields:
        if not field.required:
            continue
        if not is_publishable_field_status(field.status):
            violations.append(PublishViolationCode.REQUIRED_FIELD_NOT_PUBLISHABLE)
        elif (
            field.status is not FieldValueStatus.VALUE_PRESENT
            and field.missing_reason is None
        ):
            violations.append(PublishViolationCode.REQUIRED_FIELD_MISSING_REASON)

    return PublishValidation(tuple(dict.fromkeys(violations)))
