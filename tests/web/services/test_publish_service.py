from __future__ import annotations

from dataclasses import replace

import pytest

from court_ocr_extract.domain.field_status import FieldMissingReason, FieldValueStatus
from court_ocr_extract.domain.publishing import (
    PublishCandidate,
    PublishField,
    PublishSourceKind,
    PublishViolationCode,
)
from court_ocr_extract.domain.workflow import WorkflowState
from court_ocr_extract.services.publish_service import (
    PublishRejected,
    PublishService,
)


class FakeUnitOfWork:
    def __init__(self, *, fail_audit: bool = False) -> None:
        self.fail_audit = fail_audit
        self.staged_core: list[str] = []
        self.committed_core: list[str] = []
        self.audit_events: list[object] = []
        self.rolled_back = False

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def write_core(self, candidate: PublishCandidate) -> str:
        self.staged_core.append(candidate.source_id)
        return "published-1"

    def append_audit(self, event: object) -> None:
        if self.fail_audit:
            raise RuntimeError("synthetic audit failure")
        self.audit_events.append(event)

    def commit(self) -> None:
        self.committed_core.extend(self.staged_core)
        self.staged_core.clear()

    def rollback(self) -> None:
        self.rolled_back = True
        self.staged_core.clear()


def approved_candidate() -> PublishCandidate:
    return PublishCandidate(
        source_kind=PublishSourceKind.REVIEW_VERSION,
        source_id="synthetic-review-1",
        state=WorkflowState.APPROVED,
        fields=(
            PublishField(
                field_key="synthetic_required",
                status=FieldValueStatus.VALUE_PRESENT,
                required=True,
            ),
        ),
        approval_id="synthetic-approval-1",
        approver_id="synthetic-actor-1",
        is_locked=True,
        schema_version="1.0.0",
    )


def test_machine_extraction_cannot_publish_directly() -> None:
    candidate = replace(
        approved_candidate(),
        source_kind=PublishSourceKind.MACHINE_EXTRACTION,
    )
    service = PublishService(FakeUnitOfWork)

    with pytest.raises(PublishRejected) as error:
        service.publish(candidate)

    assert (
        PublishViolationCode.MACHINE_EXTRACTION_NOT_PUBLISHABLE
        in error.value.violation_codes
    )


@pytest.mark.parametrize(
    ("candidate", "expected_violation"),
    [
        (
            replace(approved_candidate(), state=WorkflowState.DRAFT),
            PublishViolationCode.STATE_NOT_APPROVED,
        ),
        (
            replace(approved_candidate(), state=WorkflowState.PROCESSING),
            PublishViolationCode.STATE_NOT_APPROVED,
        ),
        (
            replace(approved_candidate(), state=WorkflowState.PENDING_REVIEW),
            PublishViolationCode.STATE_NOT_APPROVED,
        ),
        (
            replace(approved_candidate(), state=WorkflowState.IN_REVIEW),
            PublishViolationCode.STATE_NOT_APPROVED,
        ),
        (
            replace(approved_candidate(), state=WorkflowState.REJECTED),
            PublishViolationCode.STATE_NOT_APPROVED,
        ),
        (
            replace(approved_candidate(), approval_id=None),
            PublishViolationCode.APPROVAL_MISSING,
        ),
        (
            replace(approved_candidate(), approver_id=None),
            PublishViolationCode.APPROVER_MISSING,
        ),
        (
            replace(approved_candidate(), critical_warning_count=1),
            PublishViolationCode.CRITICAL_WARNINGS_UNRESOLVED,
        ),
        (
            replace(approved_candidate(), is_locked=False),
            PublishViolationCode.SNAPSHOT_NOT_LOCKED,
        ),
        (
            replace(approved_candidate(), schema_version=None),
            PublishViolationCode.SCHEMA_VERSION_MISSING,
        ),
        (
            replace(approved_candidate(), is_published=True),
            PublishViolationCode.ALREADY_PUBLISHED,
        ),
        (
            replace(
                approved_candidate(),
                fields=(
                    PublishField(
                        field_key="synthetic_required",
                        status=FieldValueStatus.PENDING_REVIEW,
                        required=True,
                    ),
                ),
            ),
            PublishViolationCode.REQUIRED_FIELD_NOT_PUBLISHABLE,
        ),
        (
            replace(
                approved_candidate(),
                fields=(
                    PublishField(
                        field_key="synthetic_required",
                        status=FieldValueStatus.NOT_IN_DOCUMENT,
                        required=True,
                    ),
                ),
            ),
            PublishViolationCode.REQUIRED_FIELD_MISSING_REASON,
        ),
    ],
)
def test_publish_guard_rejects_each_required_precondition(
    candidate: PublishCandidate,
    expected_violation: PublishViolationCode,
) -> None:
    with pytest.raises(PublishRejected) as error:
        PublishService(FakeUnitOfWork).publish(candidate)
    assert expected_violation in error.value.violation_codes


def test_required_blank_field_is_allowed_only_with_missing_reason() -> None:
    candidate = replace(
        approved_candidate(),
        fields=(
            PublishField(
                field_key="synthetic_required",
                status=FieldValueStatus.NOT_IN_DOCUMENT,
                required=True,
                missing_reason=FieldMissingReason.NOT_IN_DOCUMENT,
            ),
        ),
    )
    result = PublishService(FakeUnitOfWork).publish(candidate)
    assert result.published_record_id == "published-1"


def test_publish_commits_core_and_audit_together() -> None:
    unit_of_work = FakeUnitOfWork()
    result = PublishService(lambda: unit_of_work).publish(approved_candidate())

    assert result.published_record_id == "published-1"
    assert unit_of_work.committed_core == ["synthetic-review-1"]
    assert len(unit_of_work.audit_events) == 1


def test_audit_failure_rolls_back_core_write() -> None:
    unit_of_work = FakeUnitOfWork(fail_audit=True)

    with pytest.raises(RuntimeError, match="synthetic audit failure"):
        PublishService(lambda: unit_of_work).publish(approved_candidate())

    assert unit_of_work.rolled_back is True
    assert unit_of_work.staged_core == []
    assert unit_of_work.committed_core == []
