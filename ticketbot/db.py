import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from ticketbot.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('flight', 'train')),
    from_code TEXT NOT NULL,
    from_name TEXT NOT NULL,
    to_code TEXT NOT NULL,
    to_name TEXT NOT NULL,
    travel_date TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_checked_at TEXT,
    last_error TEXT
);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def add_subscription(chat_id: int, kind: str, from_code: str, from_name: str,
                      to_code: str, to_name: str, travel_date: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO subscriptions
               (chat_id, kind, from_code, from_name, to_code, to_name, travel_date, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (chat_id, kind, from_code, from_name, to_code, to_name, travel_date,
             datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid


def list_active_subscriptions() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM subscriptions WHERE active = 1 ORDER BY id"
        ).fetchall()


def list_user_subscriptions(chat_id: int) -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM subscriptions WHERE chat_id = ? AND active = 1 ORDER BY id",
            (chat_id,),
        ).fetchall()


def get_subscription(sub_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM subscriptions WHERE id = ?", (sub_id,)
        ).fetchone()


def deactivate_subscription(sub_id: int) -> None:
    with _connect() as conn:
        conn.execute("UPDATE subscriptions SET active = 0 WHERE id = ?", (sub_id,))


def mark_checked(sub_id: int, error: str | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE subscriptions SET last_checked_at = ?, last_error = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), error, sub_id),
        )
