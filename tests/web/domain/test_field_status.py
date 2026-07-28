from __future__ import annotations

import pytest

from court_ocr_extract.domain.field_status import (
    FieldMissingReason,
    FieldValue,
    FieldValueStatus,
    FieldValueValidationError,
    is_publishable_field_status,
)


def test_field_value_status_contract_is_exact() -> None:
    assert [status.value for status in FieldValueStatus] == [
        "VALUE_PRESENT",
        "NOT_IN_DOCUMENT",
        "OCR_UNREADABLE",
        "EXTRACTION_FAILED",
        "CONFLICTING_EVIDENCE",
        "PENDING_REVIEW",
        "REJECTED_VALUE",
        "NOT_APPLICABLE",
    ]
    assert {reason.value for reason in FieldMissingReason} == {
        "NOT_IN_DOCUMENT",
        "OCR_UNREADABLE",
        "EXTRACTION_FAILED",
        "CONFLICTING_EVIDENCE",
        "REJECTED_VALUE",
        "NOT_APPLICABLE",
    }


def test_present_value_and_missing_reason_invariants() -> None:
    assert FieldValue(FieldValueStatus.VALUE_PRESENT, value="synthetic-value").value
    assert FieldValue(
        FieldValueStatus.NOT_IN_DOCUMENT,
        missing_reason=FieldMissingReason.NOT_IN_DOCUMENT,
    ).value is None

    with pytest.raises(FieldValueValidationError):
        FieldValue(FieldValueStatus.VALUE_PRESENT, value=" ")
    with pytest.raises(FieldValueValidationError):
        FieldValue(FieldValueStatus.NOT_IN_DOCUMENT)
    with pytest.raises(FieldValueValidationError):
        FieldValue(
            FieldValueStatus.OCR_UNREADABLE,
            missing_reason=FieldMissingReason.NOT_IN_DOCUMENT,
        )


def test_unresolved_or_rejected_statuses_are_not_publishable() -> None:
    for status in (
        FieldValueStatus.PENDING_REVIEW,
        FieldValueStatus.EXTRACTION_FAILED,
        FieldValueStatus.CONFLICTING_EVIDENCE,
        FieldValueStatus.REJECTED_VALUE,
    ):
        assert not is_publishable_field_status(status)

    assert is_publishable_field_status(FieldValueStatus.VALUE_PRESENT)
    assert is_publishable_field_status(FieldValueStatus.NOT_APPLICABLE)
