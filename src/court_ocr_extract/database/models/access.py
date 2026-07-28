from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from court_ocr_extract.database.base import Base, MutableRecordMixin


ROLE_CODES = (
    "operator",
    "reviewer",
    "approver",
    "project_admin",
    "system_admin",
)


class User(MutableRecordMixin, Base):
    """Application principal identified by an opaque identity-provider key."""

    __tablename__ = "app_user"
    __table_args__ = (
        UniqueConstraint("subject_key"),
        Index("ix_audit_app_user_status", "status"),
        {"schema": "audit"},
    )

    subject_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )
    last_authenticated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Role(MutableRecordMixin, Base):
    """Named authorization role assignable to an application principal."""

    __tablename__ = "access_role"
    __table_args__ = (
        UniqueConstraint("code"),
        CheckConstraint(
            "code IN ('operator', 'reviewer', 'approver', "
            "'project_admin', 'system_admin')"
        ),
        Index("ix_audit_access_role_status", "status"),
        {"schema": "audit"},
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )


class UserRole(MutableRecordMixin, Base):
    """Versioned role grant for a principal."""

    __tablename__ = "app_user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id"),
        Index(
            "ix_audit_app_user_role_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_audit_app_user_role_role_status",
            "role_id",
            "status",
        ),
        {"schema": "audit"},
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("audit.app_user.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("audit.access_role.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("audit.app_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# Backward-compatible import names for the model aggregator.
AppUser = User
AccessRole = Role
AppUserRole = UserRole


# Domain-facing aliases retain the task vocabulary while table names stay explicit.
User = AppUser
Role = AccessRole
UserRole = AppUserRole
