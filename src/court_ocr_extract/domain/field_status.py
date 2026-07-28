from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FieldValueStatus(str, Enum):
    VALUE_PRESENT = "VALUE_PRESENT"
    NOT_IN_DOCUMENT = "NOT_IN_DOCUMENT"
    OCR_UNREADABLE = "OCR_UNREADABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED_VALUE = "REJECTED_VALUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FieldMissingReason(str, Enum):
    NOT_IN_DOCUMENT = "NOT_IN_DOCUMENT"
    OCR_UNREADABLE = "OCR_UNREADABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    REJECTED_VALUE = "REJECTED_VALUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FieldValueValidationError(ValueError):
    pass


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


@dataclass(frozen=True)
class FieldValue:
    status: FieldValueStatus
    value: Any = None
    missing_reason: FieldMissingReason | None = None

    def __post_init__(self) -> None:
        if self.status is FieldValueStatus.VALUE_PRESENT:
            if _is_blank(self.value):
                raise FieldValueValidationError("VALUE_PRESENT requires a non-blank value.")
            if self.missing_reason is not None:
                raise FieldValueValidationError(
                    "VALUE_PRESENT cannot carry a missing reason."
                )
            return

        if not _is_blank(self.value):
            raise FieldValueValidationError(
                f"{self.status.value} cannot carry a field value."
            )

        if self.status is FieldValueStatus.PENDING_REVIEW:
            if self.missing_reason is not None:
                raise FieldValueValidationError(
                    "PENDING_REVIEW is a workflow state, not a missing reason."
                )
            return

        expected_reason = FieldMissingReason(self.status.value)
        if self.missing_reason is not expected_reason:
            raise FieldValueValidationError(
                f"{self.status.value} requires missing_reason={expected_reason.value}."
            )


def is_resolved_field_status(status: FieldValueStatus) -> bool:
    return status not in {
        FieldValueStatus.PENDING_REVIEW,
        FieldValueStatus.EXTRACTION_FAILED,
        FieldValueStatus.CONFLICTING_EVIDENCE,
    }


def is_publishable_field_status(status: FieldValueStatus) -> bool:
    return status in {
        FieldValueStatus.VALUE_PRESENT,
        FieldValueStatus.NOT_IN_DOCUMENT,
        FieldValueStatus.OCR_UNREADABLE,
        FieldValueStatus.NOT_APPLICABLE,
    }
