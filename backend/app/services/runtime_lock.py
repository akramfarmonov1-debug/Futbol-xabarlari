"""Bir nechta Render instance fon vazifasini takror ishga tushirmasligi uchun lock."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from ..database import engine

BOT_LOCK_ID = 7_301_001
PIPELINE_LOCK_ID = 7_301_002


@dataclass
class RuntimeLock:
    lock_id: int
    acquired: bool
    connection: Connection | None = None


def try_runtime_lock(lock_id: int) -> RuntimeLock:
    """PostgreSQL advisory lock oladi; lokal SQLite muhitida no-op."""
    if engine.dialect.name != "postgresql":
        return RuntimeLock(lock_id=lock_id, acquired=True)

    connection = None
    try:
        connection = engine.connect()
        acquired = bool(
            connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": lock_id},
            ).scalar()
        )
        if not acquired:
            connection.close()
            connection = None
        return RuntimeLock(
            lock_id=lock_id,
            acquired=acquired,
            connection=connection,
        )
    except SQLAlchemyError as error:
        if connection is not None:
            connection.close()
        print(f"Fon vazifasi lock xatosi: {error}")
        return RuntimeLock(lock_id=lock_id, acquired=False)


def release_runtime_lock(lock: RuntimeLock) -> None:
    if lock.connection is None:
        return
    try:
        lock.connection.execute(
            text("SELECT pg_advisory_unlock(:lock_id)"),
            {"lock_id": lock.lock_id},
        )
    except SQLAlchemyError as error:
        print(f"Fon vazifasi lockini bo'shatish xatosi: {error}")
    finally:
        lock.connection.close()
