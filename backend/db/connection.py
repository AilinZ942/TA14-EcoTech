"""PostgreSQL connection helpers.

We keep the interface small and stable for the rest of the backend.
Each request opens a dedicated connection and closes it after use.
"""

from contextlib import contextmanager
import os

import psycopg2
import psycopg2.extras

def _connect():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "mydb"),
        user=os.environ.get("DB_USER", "myuser"),
        password=os.environ.get("DB_PASSWORD", "mypassword"),
        sslmode=os.environ.get("DB_SSLMODE", "prefer"),
    )


@contextmanager
def get_cursor(dict_rows: bool = True):
    """Yield (conn, cursor) and ensure proper cleanup."""

    conn = _connect()

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
        conn.close()
