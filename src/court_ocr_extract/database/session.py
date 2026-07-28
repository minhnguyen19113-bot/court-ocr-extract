from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseSettings(BaseSettings):
    """Production settings with no implicit development database."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=None,
        extra="ignore",
        case_sensitive=True,
    )

    database_url: str = Field(validation_alias="DATABASE_URL", min_length=1)


def create_database_engine(
    database_url: str | None = None,
    **engine_options: object,
) -> Engine:
    """Create an engine lazily; importing this module never opens a connection."""

    explicit_url = database_url or DatabaseSettings().database_url
    return create_engine(explicit_url, pool_pre_ping=True, **engine_options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
