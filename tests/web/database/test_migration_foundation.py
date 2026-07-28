from __future__ import annotations

import ast
from pathlib import Path

from court_ocr_extract.database.metadata import LOGICAL_SCHEMAS


ROOT = Path(__file__).resolve().parents[3]


def test_alembic_uses_explicit_database_url_and_all_schemas() -> None:
    config = (ROOT / "alembic.ini").read_text(encoding="utf-8")
    env = (ROOT / "alembic" / "env.py").read_text(encoding="utf-8")

    assert "sqlalchemy.url =" in config
    assert "sqlite://" not in config
    assert 'os.environ.get("DATABASE_URL")' in env
    assert "include_schemas=True" in env
    assert "DATABASE_URL is required" in env


def test_baseline_only_creates_and_drops_six_logical_schemas() -> None:
    path = ROOT / "alembic" / "versions" / "0001_phase0_foundation.py"
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    assigned_schemas: tuple[str, ...] | None = None
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "LOGICAL_SCHEMAS"
            for target in node.targets
        ):
            assigned_schemas = ast.literal_eval(node.value)

    assert assigned_schemas == LOGICAL_SCHEMAS
    assert "CreateSchema" in source
    assert "DropSchema" in source
    assert "op.create_table" not in source
    assert "0002_phase0_tables" in source


def test_table_migration_is_explicit_complete_and_reversible() -> None:
    path = ROOT / "alembic" / "versions" / "0002_phase0_tables.py"
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    assignments = {
        target.id: ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.AnnAssign)
        and isinstance((target := node.target), ast.Name)
        and target.id in {"revision", "down_revision"}
    }

    assert assignments == {
        "revision": "0002_phase0_tables",
        "down_revision": "0001_phase0_foundation",
    }
    assert source.count("op.create_table(") == 39
    assert source.count("op.drop_table(") == 39
    assert "metadata.create_all" not in source
    assert "court_ocr_extract.database" not in source
