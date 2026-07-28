from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from court_ocr_extract.database.base import (
    JSON_VALUE,
    Base,
    MutableRecordMixin,
    utc_now,
)


class ReviewTask(MutableRecordMixin, Base):
    __tablename__ = "review_task"
    __table_args__ = (
        UniqueConstraint("task_key", name="uq_review_review_task_task_key"),
        Index(
            "ix_review_review_task_status_priority",
            "status",
            "priority",
        ),
        Index(
            "ix_review_review_task_assignee_status",
            "assigned_to_user_id",
            "status",
        ),
        {"schema": "review"},
    )

    task_key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ReviewVersion(MutableRecordMixin, Base):
    __tablename__ = "review_version"
    __table_args__ = (
        UniqueConstraint(
            "review_task_id",
            "version",
            name="uq_review_review_version_task_version",
        ),
        Index(
            "ix_review_review_version_extraction_snapshot",
            "extraction_snapshot_id",
        ),
        Index(
            "ix_review_review_version_status_locked",
            "status",
            "locked",
        ),
        Index(
            "ix_review_review_version_supersedes",
            "supersedes_review_version_id",
        ),
        {"schema": "review"},
    )

    review_task_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_task.id", ondelete="RESTRICT"),
        nullable=False,
    )
    extraction_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing.extraction_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_id: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    case_domain: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="draft",
        nullable=False,
    )
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    locked_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=True,
    )
    supersedes_review_version_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_version.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    review_payload: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class FieldReview(MutableRecordMixin, Base):
    __tablename__ = "field_review"
    __table_args__ = (
        UniqueConstraint(
            "review_version_id",
            "field_path",
            name="uq_review_field_review_version_path",
        ),
        UniqueConstraint(
            "review_version_id",
            "extracted_field_id",
            name="uq_review_field_review_version_machine_field",
        ),
        Index(
            "ix_review_field_review_status",
            "review_version_id",
            "review_status",
        ),
        Index(
            "ix_review_field_review_machine_field",
            "extracted_field_id",
        ),
        Index(
            "ix_review_field_review_reviewer",
            "reviewed_by_user_id",
            "reviewed_at",
        ),
        {"schema": "review"},
    )

    review_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    extracted_field_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("processing.extracted_field.id", ondelete="RESTRICT"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    field_path: Mapped[str] = mapped_column(String(512), nullable=False)
    machine_value: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    reviewed_value: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    machine_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
    )
    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 5),
        nullable=True,
    )
    evidence: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class FieldCorrection(MutableRecordMixin, Base):
    __tablename__ = "field_correction"
    __table_args__ = (
        UniqueConstraint(
            "field_review_id",
            "version",
            name="uq_review_field_correction_review_number",
        ),
        Index(
            "ix_review_field_correction_version",
            "review_version_id",
            "corrected_at",
        ),
        Index(
            "ix_review_field_correction_actor",
            "corrected_by_user_id",
            "corrected_at",
        ),
        {"schema": "review"},
    )

    review_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    field_review_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.field_review.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_value: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    corrected_value: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class ReviewComment(MutableRecordMixin, Base):
    __tablename__ = "review_comment"
    __table_args__ = (
        UniqueConstraint(
            "review_version_id",
            "comment_number",
            name="uq_review_review_comment_version_number",
        ),
        Index(
            "ix_review_review_comment_field",
            "field_review_id",
            "created_at",
        ),
        Index(
            "ix_review_review_comment_author",
            "author_user_id",
            "created_at",
        ),
        {"schema": "review"},
    )

    review_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    field_review_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.field_review.id", ondelete="RESTRICT"),
        nullable=True,
    )
    parent_comment_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_comment.id", ondelete="RESTRICT"),
        nullable=True,
    )
    comment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Approval(MutableRecordMixin, Base):
    __tablename__ = "approval"
    __table_args__ = (
        UniqueConstraint(
            "review_version_id",
            name="uq_review_approval_review_version",
        ),
        Index(
            "ix_review_approval_decision",
            "review_version_id",
            "decision",
        ),
        Index(
            "ix_review_approval_actor",
            "approved_by_user_id",
            "approved_at",
        ),
        {"schema": "review"},
    )

    review_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    schema_id: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit.app_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
