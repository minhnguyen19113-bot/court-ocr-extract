from __future__ import annotations

from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from court_ocr_extract.database.metadata import (
    LOGICAL_SCHEMAS,
    SQLITE_SCHEMA_TRANSLATE_MAP,
    get_metadata,
)


REQUIRED_TABLES = {
    "audit.app_user",
    "audit.access_role",
    "audit.app_user_role",
    "audit.audit_event",
    "ingest.job",
    "ingest.document",
    "ingest.document_version",
    "ingest.document_page",
    "ingest.artifact",
    "processing.processing_run",
    "processing.pipeline_step",
    "processing.extraction_snapshot",
    "processing.extracted_entity",
    "processing.extracted_field",
    "processing.evidence_ref",
    "processing.extraction_warning",
    "review.review_task",
    "review.review_version",
    "review.field_review",
    "review.field_correction",
    "review.review_comment",
    "review.approval",
    "core.published_snapshot",
    "core.court_case",
    "core.judgment",
    "core.person",
    "core.case_party",
    "core.charge",
    "core.sentence",
    "core.address",
    "core.source_document_link",
    "forms.form_catalog_entry",
    "forms.form_template",
    "forms.form_template_version",
    "forms.form_definition",
    "forms.form_field_definition",
    "forms.form_field_mapping",
    "forms.form_generation_request",
    "forms.generated_document",
}


def test_all_models_import_and_register_required_tables() -> None:
    metadata = get_metadata()

    assert LOGICAL_SCHEMAS == (
        "ingest",
        "processing",
        "review",
        "core",
        "forms",
        "audit",
    )
    assert REQUIRED_TABLES == set(metadata.tables)


def test_metadata_creates_on_explicit_sqlite_test_engine() -> None:
    metadata = get_metadata()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    translated = engine.execution_options(
        schema_translate_map=SQLITE_SCHEMA_TRANSLATE_MAP
    )

    metadata.create_all(translated)

    assert set(inspect(translated).get_table_names()) == {
        table.name for table in metadata.tables.values()
    }


def test_snapshot_and_document_versions_are_explicit() -> None:
    metadata = get_metadata()
    expected_version_columns = {
        "ingest.document_version": "version_number",
        "processing.processing_run": "run_version",
        "processing.extraction_snapshot": "snapshot_version",
        "review.review_version": "version",
        "core.published_snapshot": "version",
        "forms.form_template_version": "version",
        "forms.generated_document": "version",
    }

    for table_name, column_name in expected_version_columns.items():
        assert column_name in metadata.tables[table_name].c, table_name


def test_all_tables_and_indexes_compile_for_postgresql() -> None:
    metadata = get_metadata()
    dialect = postgresql.dialect()
    statements = []

    for table in metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=dialect)))
        statements.extend(
            str(CreateIndex(index).compile(dialect=dialect))
            for index in table.indexes
        )

    assert len(statements) > len(metadata.tables)
