from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from court_ocr_extract.database.base import JSON_VALUE, Base, ImmutableRecordMixin


class AuditEvent(ImmutableRecordMixin, Base):
    """Append-only event containing identifiers and safe metadata only."""

    __tablename__ = "audit_event"
    __table_args__ = (
        Index("ix_audit_audit_event_subject", "subject_type", "subject_id"),
        Index("ix_audit_audit_event_correlation", "correlation_id"),
        {"schema": "audit"},
    )

    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("audit.app_user.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_id: Mapped[UUID | None] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS")
    correlation_id: Mapped[str | None] = mapped_column(String(120))
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )
