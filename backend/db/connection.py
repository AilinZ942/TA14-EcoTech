"""PostgreSQL connection pool.

A single global pool is created at startup and shared by all requests.
"""

from contextlib import contextmanager
import os

import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool

_pool: pg_pool.SimpleConnectionPool | None = None


def init_pool() -> None:
    global _pool

    if _pool is not None:
        return

    _pool = pg_pool.SimpleConnectionPool(
        minconn=int(os.environ.get("DB_POOL_MIN", "1")),
        maxconn=int(os.environ.get("DB_POOL_MAX", "10")),
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "mydb"),
        user=os.environ.get("DB_USER", "myuser"),
        password=os.environ.get("DB_PASSWORD", "mypassword"),
        sslmode=os.environ.get("DB_SSLMODE", "prefer"),
    )


def close_pool() -> None:
    global _pool

    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_cursor(dict_rows: bool = True):
    """Yield (conn, cursor) and ensure proper cleanup."""

    if _pool is None:
        init_pool()

    conn = _pool.getconn()

    try:
        cursor_factory = psycopg2.extras.RealDictCursor if dict_rows else None
        cur = conn.cursor(cursor_factory=cursor_factory)

        try:
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    finally:
        _pool.putconn(conn)
