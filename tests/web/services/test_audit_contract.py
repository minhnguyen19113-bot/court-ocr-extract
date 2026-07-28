from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from court_ocr_extract.domain.audit import AppendOnlyAuditLog, AuditEvent


def test_audit_event_is_frozen() -> None:
    event = AuditEvent(
        event_type="SYNTHETIC_EVENT",
        actor_id="synthetic-actor",
        subject_type="synthetic_subject",
        subject_id="synthetic-id",
    )

    with pytest.raises(FrozenInstanceError):
        event.event_type = "CHANGED"  # type: ignore[misc]


def test_append_only_contract_has_no_update_or_delete() -> None:
    assert "append" in AppendOnlyAuditLog.__dict__
    assert "update" not in AppendOnlyAuditLog.__dict__
    assert "delete" not in AppendOnlyAuditLog.__dict__
