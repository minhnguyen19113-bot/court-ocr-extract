from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Integer, MetaData, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _schema_token(constraint: Any, table: Any) -> str:
    return table.schema or "default"


NAMING_CONVENTION = {
    "schema": _schema_token,
    "ix": "ix_%(schema)s_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(schema)s_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(schema)s_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(schema)s_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(schema)s_%(table_name)s",
}

JSON_VALUE = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class OptimisticLockMixin:
    lock_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class MutableRecordMixin(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OptimisticLockMixin,
):
    pass


class ImmutableRecordMixin(UUIDPrimaryKeyMixin, CreatedAtMixin):
    pass
