from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Date,
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


class PublishedSnapshot(MutableRecordMixin, Base):
    __tablename__ = "published_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "review_version_id",
            name="uq_core_published_snapshot_review_version",
        ),
        UniqueConstraint(
            "approval_id",
            name="uq_core_published_snapshot_approval",
        ),
        Index(
            "ix_core_published_snapshot_status_time",
            "status",
            "published_at",
        ),
        {"schema": "core"},
    )

    review_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.review_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approval_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review.approval.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_id: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    case_domain: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="published",
        nullable=False,
    )
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class CourtCase(MutableRecordMixin, Base):
    __tablename__ = "court_case"
    __table_args__ = (
        UniqueConstraint(
            "published_snapshot_id",
            "case_number",
            name="uq_core_court_case_snapshot_number",
        ),
        Index(
            "ix_core_court_case_snapshot_status",
            "published_snapshot_id",
            "status",
        ),
        Index(
            "ix_core_court_case_court",
            "court_name",
            "adjudicated_on",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    case_number: Mapped[str] = mapped_column(String(255), nullable=False)
    case_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    court_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    filed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    adjudicated_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class Judgment(MutableRecordMixin, Base):
    __tablename__ = "judgment"
    __table_args__ = (
        UniqueConstraint(
            "published_snapshot_id",
            "judgment_number",
            name="uq_core_judgment_snapshot_number",
        ),
        Index(
            "ix_core_judgment_case_date",
            "court_case_id",
            "judgment_date",
        ),
        Index(
            "ix_core_judgment_snapshot",
            "published_snapshot_id",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    court_case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.court_case.id", ondelete="RESTRICT"),
        nullable=False,
    )
    judgment_number: Mapped[str] = mapped_column(String(255), nullable=False)
    judgment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    judgment_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)


class Person(MutableRecordMixin, Base):
    __tablename__ = "person"
    __table_args__ = (
        UniqueConstraint(
            "published_snapshot_id",
            "person_key",
            name="uq_core_person_snapshot_key",
        ),
        Index(
            "ix_core_person_snapshot_name",
            "published_snapshot_id",
            "full_name",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    person_key: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    identity_document_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    identity_document_number: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )


class CaseParty(MutableRecordMixin, Base):
    __tablename__ = "case_party"
    __table_args__ = (
        UniqueConstraint(
            "court_case_id",
            "party_number",
            name="uq_core_case_party_case_number",
        ),
        Index(
            "ix_core_case_party_snapshot_role",
            "published_snapshot_id",
            "role",
        ),
        Index(
            "ix_core_case_party_person",
            "person_id",
            "court_case_id",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    court_case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.court_case.id", ondelete="RESTRICT"),
        nullable=False,
    )
    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.person.id", ondelete="RESTRICT"),
        nullable=False,
    )
    party_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    details: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)


class Charge(MutableRecordMixin, Base):
    __tablename__ = "charge"
    __table_args__ = (
        UniqueConstraint(
            "court_case_id",
            "charge_number",
            name="uq_core_charge_case_number",
        ),
        Index(
            "ix_core_charge_snapshot",
            "published_snapshot_id",
        ),
        Index(
            "ix_core_charge_party",
            "case_party_id",
            "disposition",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    court_case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.court_case.id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_party_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.case_party.id", ondelete="RESTRICT"),
        nullable=False,
    )
    charge_number: Mapped[int] = mapped_column(Integer, nullable=False)
    charge_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    charge_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    legal_provision: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposition: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Sentence(MutableRecordMixin, Base):
    __tablename__ = "sentence"
    __table_args__ = (
        UniqueConstraint(
            "judgment_id",
            "sentence_number",
            name="uq_core_sentence_judgment_number",
        ),
        Index(
            "ix_core_sentence_snapshot",
            "published_snapshot_id",
        ),
        Index(
            "ix_core_sentence_party_type",
            "case_party_id",
            "sentence_type",
        ),
        Index(
            "ix_core_sentence_charge",
            "charge_id",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    judgment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.judgment.id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_party_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.case_party.id", ondelete="RESTRICT"),
        nullable=False,
    )
    charge_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.charge.id", ondelete="RESTRICT"),
        nullable=True,
    )
    sentence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sentence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fine_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
    )
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class Address(MutableRecordMixin, Base):
    __tablename__ = "address"
    __table_args__ = (
        UniqueConstraint(
            "person_id",
            "address_number",
            name="uq_core_address_person_number",
        ),
        Index(
            "ix_core_address_snapshot",
            "published_snapshot_id",
        ),
        Index(
            "ix_core_address_admin",
            "province",
            "district",
            "ward",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.person.id", ondelete="RESTRICT"),
        nullable=False,
    )
    address_number: Mapped[int] = mapped_column(Integer, nullable=False)
    address_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ward: Mapped[str | None] = mapped_column(String(128), nullable=True)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)


class SourceDocumentLink(MutableRecordMixin, Base):
    __tablename__ = "source_document_link"
    __table_args__ = (
        UniqueConstraint(
            "published_snapshot_id",
            "document_version_id",
            "entity_type",
            "entity_id",
            "source_page_start",
            "source_page_end",
            name="uq_core_source_document_link_evidence",
        ),
        Index(
            "ix_core_source_document_link_document",
            "document_version_id",
            "source_page_start",
        ),
        Index(
            "ix_core_source_document_link_entity",
            "published_snapshot_id",
            "entity_type",
            "entity_id",
        ),
        {"schema": "core"},
    )

    published_snapshot_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("core.published_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ingest.document_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_locator: Mapped[Any | None] = mapped_column(JSON_VALUE, nullable=True)
