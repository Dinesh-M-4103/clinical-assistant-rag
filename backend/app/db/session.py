"""Engine and session construction for the SQLite database."""

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


def create_db_engine(database_url: str) -> Engine:
    """Create an engine whose connections enforce foreign keys and use WAL.

    SQLite ignores foreign keys unless asked per connection, and WAL lets the
    chat endpoints read while an upload is writing.
    """
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    """Create missing tables. There are no migrations: the schema is two small tables."""
    if engine.url.database:
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)
    from app.db import models  # noqa: F401  (registers the tables on Base.metadata)

    Base.metadata.create_all(engine)
