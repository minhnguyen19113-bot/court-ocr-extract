from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4


AuditMetadata = tuple[tuple[str, str], ...]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor_id: str
    subject_type: str
    subject_id: str
    metadata: AuditMetadata = ()
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=_utc_now)


class AppendOnlyAuditLog(Protocol):
    """Audit sink intentionally exposes append and no update/delete operation."""

    def append(self, event: AuditEvent) -> None: ...
