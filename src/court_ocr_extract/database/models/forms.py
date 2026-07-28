from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from court_ocr_extract.database.base import JSON_VALUE, Base, MutableRecordMixin


class FormCatalogEntry(MutableRecordMixin, Base):
    __tablename__ = "form_catalog_entry"
    __table_args__ = (
        UniqueConstraint("code"),
        Index("ix_forms_form_catalog_entry_domain_status", "case_domain", "status"),
        {"schema": "forms"},
    )

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    case_domain: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class FormTemplate(MutableRecordMixin, Base):
    __tablename__ = "form_template"
    __table_args__ = (
        UniqueConstraint("catalog_entry_id", "name"),
        {"schema": "forms"},
    )

    catalog_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_catalog_entry.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class FormTemplateVersion(MutableRecordMixin, Base):
    __tablename__ = "form_template_version"
    __table_args__ = (
        UniqueConstraint("template_id", "version"),
        CheckConstraint(
            "adapter_status IN "
            "('NOT_IMPLEMENTED', 'DECLARED', 'AVAILABLE', 'UNAVAILABLE')",
            name="ck_forms_form_template_version_adapter_status",
        ),
        {"schema": "forms"},
    )

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_template.id"), nullable=False, index=True
    )
    artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.artifact.id"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    template_format: Mapped[str] = mapped_column(String(32), nullable=False)
    adapter_type: Mapped[str] = mapped_column(String(32), nullable=False)
    adapter_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="DECLARED"
    )
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class FormDefinition(MutableRecordMixin, Base):
    __tablename__ = "form_definition"
    __table_args__ = (
        UniqueConstraint("definition_key", "version"),
        {"schema": "forms"},
    )

    catalog_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_catalog_entry.id"), nullable=False, index=True
    )
    template_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_template_version.id"), nullable=False, index=True
    )
    definition_key: Mapped[str] = mapped_column(String(120), nullable=False)
    schema_id: Mapped[str] = mapped_column(String(120), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class FormFieldDefinition(MutableRecordMixin, Base):
    __tablename__ = "form_field_definition"
    __table_args__ = (
        UniqueConstraint("form_definition_id", "field_key"),
        {"schema": "forms"},
    )

    form_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_definition.id"), nullable=False, index=True
    )
    field_key: Mapped[str] = mapped_column(String(160), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(40), nullable=False, default="string")
    output_placeholder: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_manual_input: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class FormFieldMapping(MutableRecordMixin, Base):
    __tablename__ = "form_field_mapping"
    __table_args__ = (
        UniqueConstraint("field_definition_id", "mapping_order"),
        {"schema": "forms"},
    )

    field_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_field_definition.id"), nullable=False, index=True
    )
    mapping_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_entity: Mapped[str | None] = mapped_column(String(120))
    source_field: Mapped[str | None] = mapped_column(String(160))
    source_path: Mapped[str | None] = mapped_column(String(500))
    transformation: Mapped[str | None] = mapped_column(String(160))
    formatter: Mapped[str | None] = mapped_column(String(160))
    default_value_json: Mapped[Any | None] = mapped_column(JSON_VALUE)
    visibility_condition_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_VALUE)
    repeat_rule_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_VALUE)
    exclusion_rule_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_VALUE)
    validation_rule_json: Mapped[dict[str, Any] | None] = mapped_column(JSON_VALUE)
    instruction_removal_rule_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON_VALUE
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class FormGenerationRequest(MutableRecordMixin, Base):
    __tablename__ = "form_generation_request"
    __table_args__ = (
        CheckConstraint(
            "(approved_review_version_id IS NOT NULL "
            "AND published_snapshot_id IS NULL) OR "
            "(approved_review_version_id IS NULL "
            "AND published_snapshot_id IS NOT NULL)",
            name="ck_forms_generation_source",
        ),
        Index("ix_forms_form_generation_request_status", "status"),
        {"schema": "forms"},
    )

    form_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_definition.id"), nullable=False, index=True
    )
    approved_review_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("review.review_version.id"), index=True
    )
    published_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("core.published_snapshot.id"), index=True
    )
    requested_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("audit.app_user.id"), nullable=False, index=True
    )
    output_format: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )


class GeneratedDocument(MutableRecordMixin, Base):
    __tablename__ = "generated_document"
    __table_args__ = (
        UniqueConstraint("generation_request_id", "version"),
        {"schema": "forms"},
    )

    generation_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("forms.form_generation_request.id"), nullable=False, index=True
    )
    artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingest.artifact.id"), nullable=False, index=True
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("audit.app_user.id"), nullable=False, index=True
    )
    output_format: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="GENERATED")
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSON_VALUE, nullable=False, default=dict
    )
