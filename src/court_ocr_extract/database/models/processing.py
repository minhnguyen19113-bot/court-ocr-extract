from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Float,
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


class ProcessingRun(MutableRecordMixin, Base):
    """Versioned execution of a processing pipeline for one document version."""

    __tablename__ = "processing_run"
    __table_args__ = (
        UniqueConstraint("run_key"),
        UniqueConstraint("document_version_id", "run_version"),
        Index(
            "ix_processing_run_document_status",
            "document_version_id",
            "status",
        ),
        Index("ix_processing_run_job_created_at", "job_id", "created_at"),
        Index("ix_processing_run_status_created_at", "status", "created_at"),
        {"schema": "processing"},
    )

    run_key: Mapped[str] = mapped_column(String(255), nullable=False)
    run_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.job.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.document_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        nullable=False,
    )
    parameters_json: Mapped[dict[str, Any]] = mapped_column(
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


class PipelineStep(MutableRecordMixin, Base):
    """One retryable step attempt within a processing run."""

    __tablename__ = "pipeline_step"
    __table_args__ = (
        UniqueConstraint("processing_run_id", "step_key", "attempt_number"),
        Index(
            "ix_processing_pipeline_step_run_status",
            "processing_run_id",
            "status",
        ),
        Index(
            "ix_processing_pipeline_step_status_created_at",
            "status",
            "created_at",
        ),
        {"schema": "processing"},
    )

    processing_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.processing_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    step_version: Mapped[str] = mapped_column(String(100), nullable=False)
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        nullable=False,
    )
    metrics_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE,
        default=dict,
        nullable=False,
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ExtractionSnapshot(ImmutableRecordMixin, Base):
    """Immutable extraction boundary produced by a completed pipeline step."""

    __tablename__ = "extraction_snapshot"
    __table_args__ = (
        UniqueConstraint("processing_run_id", "snapshot_version"),
        Index(
            "ix_processing_extraction_snapshot_run_status",
            "processing_run_id",
            "status",
        ),
        Index(
            "ix_processing_extraction_snapshot_document_created_at",
            "document_version_id",
            "created_at",
        ),
        {"schema": "processing"},
    )

    processing_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.processing_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.document_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    produced_by_step_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.pipeline_step.id", ondelete="RESTRICT"),
        nullable=False,
    )
    snapshot_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    schema_id: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    case_domain: Mapped[str] = mapped_column(
        String(32),
        default="criminal",
        nullable=False,
    )
    is_machine_output: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="created",
        nullable=False,
    )


class ExtractedEntity(ImmutableRecordMixin, Base):
    """Typed entity captured inside an immutable extraction snapshot."""

    __tablename__ = "extracted_entity"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "entity_type", "ordinal"),
        Index(
            "ix_processing_extracted_entity_snapshot_status",
            "snapshot_id",
            "status",
        ),
        {"schema": "processing"},
    )

    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.extraction_snapshot.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="extracted",
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class ExtractedField(ImmutableRecordMixin, Base):
    """A structured field value; raw OCR text is deliberately not persisted."""

    __tablename__ = "extracted_field"
    __table_args__ = (
        UniqueConstraint("entity_id", "field_key", "occurrence"),
        Index(
            "ix_processing_extracted_field_entity_status",
            "entity_id",
            "field_status",
        ),
        {"schema": "processing"},
    )

    entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.extracted_entity.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    occurrence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    machine_value: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
    normalized_machine_value: Mapped[Any | None] = mapped_column(
        JSON_VALUE,
        nullable=True,
    )
    field_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING_REVIEW",
        nullable=False,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class EvidenceRef(ImmutableRecordMixin, Base):
    """Non-textual evidence locator for an extracted field."""

    __tablename__ = "evidence_ref"
    __table_args__ = (
        UniqueConstraint("extracted_field_id", "rank"),
        Index(
            "ix_processing_evidence_ref_field_status",
            "extracted_field_id",
            "status",
        ),
        Index("ix_processing_evidence_ref_page", "document_page_id"),
        {"schema": "processing"},
    )

    extracted_field_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.extracted_field.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_page_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.document_page.id", ondelete="RESTRICT"),
        nullable=False,
    )
    artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.artifact.id", ondelete="RESTRICT"),
        nullable=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    locator_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE,
        default=dict,
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="available",
        nullable=False,
    )


class ExtractionWarning(ImmutableRecordMixin, Base):
    """Structured extraction warning without free-form OCR content."""

    __tablename__ = "extraction_warning"
    __table_args__ = (
        Index(
            "ix_processing_extraction_warning_snapshot_severity",
            "snapshot_id",
            "severity",
        ),
        Index(
            "ix_processing_extraction_warning_field_status",
            "extracted_field_id",
            "status",
        ),
        {"schema": "processing"},
    )

    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("processing.extraction_snapshot.id", ondelete="CASCADE"),
        nullable=False,
    )
    extracted_field_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("processing.extracted_field.id", ondelete="CASCADE"),
        nullable=True,
    )
    warning_code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(32),
        default="warning",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="open",
        nullable=False,
    )
    details_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE,
        default=dict,
        nullable=False,
    )
