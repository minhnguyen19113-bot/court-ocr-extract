from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import MetaData

from court_ocr_extract.database.base import Base


LOGICAL_SCHEMAS = (
    "ingest",
    "processing",
    "review",
    "core",
    "forms",
    "audit",
)

SQLITE_SCHEMA_TRANSLATE_MAP: Mapping[str, None] = {
    schema: None for schema in LOGICAL_SCHEMAS
}


def get_metadata() -> MetaData:
    """Return the one registry after importing the model aggregator."""

    from court_ocr_extract.database import models as _models  # noqa: F401

    return Base.metadata


def schema_translate_map_for(dialect_name: str) -> Mapping[str, str | None]:
    """Flatten logical schemas only for an explicitly selected SQLite test."""

    if dialect_name == "sqlite":
        return SQLITE_SCHEMA_TRANSLATE_MAP
    return {}
