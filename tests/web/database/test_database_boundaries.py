from __future__ import annotations

import importlib

import pytest
from pydantic import ValidationError
from sqlalchemy import CheckConstraint
from sqlalchemy.engine import Engine

from court_ocr_extract.database.metadata import get_metadata
from court_ocr_extract.database.models.audit import AuditEvent
from court_ocr_extract.database.repositories import AuditEventRepository


def _foreign_key_edges() -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for table in get_metadata().tables.values():
        for foreign_key in table.foreign_keys:
            edges.add((table.fullname, foreign_key.column.table.fullname))
    return edges


def test_foreign_key_graph_has_no_machine_extraction_to_core_edge() -> None:
    edges = _foreign_key_edges()

    assert edges
    assert not {
        edge
        for edge in edges
        if edge[0].startswith("processing.") and edge[1].startswith("core.")
    }
    assert not {
        edge
        for edge in edges
        if edge[0].startswith("core.") and edge[1].startswith("processing.")
    }
    assert ("core.published_snapshot", "review.review_version") in edges
    assert ("core.published_snapshot", "review.approval") in edges


def test_generation_request_requires_exactly_one_official_source() -> None:
    table = get_metadata().tables["forms.form_generation_request"]
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    constraint_name = "ck_forms_generation_source"

    assert constraint_name in checks
    expression = " ".join(checks[constraint_name].split())
    assert "approved_review_version_id IS NOT NULL" in expression
    assert "published_snapshot_id IS NOT NULL" in expression


def test_audit_event_and_repository_are_append_only() -> None:
    assert "updated_at" not in AuditEvent.__table__.c
    assert {"append", "list"} <= set(AuditEventRepository.__dict__)
    assert {"update", "delete"}.isdisjoint(AuditEventRepository.__dict__)


def test_session_import_does_not_connect_and_missing_url_has_no_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from court_ocr_extract.database import session

    reloaded = importlib.reload(session)

    assert not any(isinstance(value, Engine) for value in vars(reloaded).values())
    with pytest.raises(ValidationError):
        reloaded.create_database_engine()
