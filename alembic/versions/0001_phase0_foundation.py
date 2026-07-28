"""Create the Phase 0 logical schemas.

The reviewed model tables are created by ``0002_phase0_tables``. This
baseline only establishes namespace ownership.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy.schema import CreateSchema, DropSchema


revision: str = "0001_phase0_foundation"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LOGICAL_SCHEMAS = (
    "ingest",
    "processing",
    "review",
    "core",
    "forms",
    "audit",
)


def upgrade() -> None:
    for schema in LOGICAL_SCHEMAS:
        op.execute(CreateSchema(schema, if_not_exists=True))


def downgrade() -> None:
    for schema in reversed(LOGICAL_SCHEMAS):
        op.execute(DropSchema(schema, if_exists=True))
