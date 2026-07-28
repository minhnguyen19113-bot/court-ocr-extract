from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from court_ocr_extract.database.base import (
    JSON_VALUE,
    Base,
    ImmutableRecordMixin,
    MutableRecordMixin,
)


class Job(MutableRecordMixin, Base):
    """One idempotently submitted ingest request."""

    __tablename__ = "job"
    __table_args__ = (
        UniqueConstraint("request_key"),
        Index("ix_ingest_job_status_created_at", "status", "created_at"),
        Index(
            "ix_ingest_job_requested_by_created_at",
            "requested_by_user_id",
            "created_at",
        ),
        {"schema": "ingest"},
    )

    request_key: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("audit.app_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    case_domain: Mapped[str] = mapped_column(
        String(32),
        default="criminal",
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    options_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE,
        default=dict,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Document(MutableRecordMixin, Base):
    """Logical document owned by an ingest job."""

    __tablename__ = "document"
    __table_args__ = (
        UniqueConstraint("job_id", "document_key"),
        Index("ix_ingest_document_job_status", "job_id", "status"),
        Index("ix_ingest_document_status_created_at", "status", "created_at"),
        {"schema": "ingest"},
    )

    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.job.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_key: Mapped[str] = mapped_column(String(255), nullable=False)
    document_kind: Mapped[str] = mapped_column(
        String(50),
        default="court_document",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="registered",
        nullable=False,
    )
    current_version_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Artifact(MutableRecordMixin, Base):
    """Metadata for an immutable blob addressed only by an opaque storage key."""

    __tablename__ = "artifact"
    __table_args__ = (
        UniqueConstraint("storage_key"),
        Index(
            "ix_ingest_artifact_type_created_at",
            "artifact_type",
            "created_at",
        ),
        Index("ix_ingest_artifact_checksum", "checksum_sha256"),
        Index("ix_ingest_artifact_job_document", "job_id", "document_id"),
        {"schema": "ingest"},
    )

    job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.job.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.document.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("audit.app_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    retention_state: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class DocumentVersion(ImmutableRecordMixin, Base):
    """Immutable version of a logical document."""

    __tablename__ = "document_version"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number"),
        UniqueConstraint("source_artifact_id"),
        Index(
            "ix_ingest_document_version_document_status",
            "document_id",
            "status",
        ),
        {"schema": "ingest"},
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.document.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.artifact.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supersedes_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.document_version.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="registered",
        nullable=False,
    )


class DocumentPage(MutableRecordMixin, Base):
    """Stable page coordinate within a document version."""

    __tablename__ = "document_page"
    __table_args__ = (
        UniqueConstraint("document_version_id", "page_number"),
        UniqueConstraint("page_artifact_id"),
        Index(
            "ix_ingest_document_page_version_status",
            "document_version_id",
            "status",
        ),
        {"schema": "ingest"},
    )

    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.document_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.artifact.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="registered",
        nullable=False,
    )
    width_pixels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_pixels: Mapped[int | None] = mapped_column(Integer, nullable=True)
