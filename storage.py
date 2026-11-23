"""SQLite storage for every user's memory and mood history.

One file, safe for concurrent API requests (WAL mode, one connection per call),
with a delete_user() for privacy requests.
"""
import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS memory (
    user_id TEXT PRIMARY KEY,
    user_name TEXT NOT NULL DEFAULT '',
    facts TEXT NOT NULL DEFAULT '[]',
    last_seen TEXT NOT NULL DEFAULT '',
    total_conversations INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS moods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    emotion TEXT NOT NULL,
    excerpt TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_moods_user ON moods(user_id, id);
"""


@contextmanager
def connect(db_path: Optional[str] = None) -> Iterator[sqlite3.Connection]:
    path = db_path or config.DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_memory(user_id: str) -> dict:
    with connect() as db:
        row = db.execute("SELECT * FROM memory WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        return {"user_name": "", "facts": [], "last_seen": "", "total_conversations": 0}
    return {"user_name": row["user_name"], "facts": json.loads(row["facts"]),
            "last_seen": row["last_seen"], "total_conversations": row["total_conversations"]}


def save_memory(user_id: str, memory: dict) -> None:
    with connect() as db:
        db.execute(
            """INSERT INTO memory (user_id, user_name, facts, last_seen, total_conversations)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET user_name=excluded.user_name, facts=excluded.facts,
                   last_seen=excluded.last_seen, total_conversations=excluded.total_conversations""",
            (user_id, memory["user_name"], json.dumps(memory["facts"][-config.MAX_FACTS:]),
             memory["last_seen"], memory["total_conversations"]),
        )


def log_mood(user_id: str, emotion: str, excerpt: str = "") -> None:
    with connect() as db:
        db.execute("INSERT INTO moods (user_id, ts, emotion, excerpt) VALUES (?, ?, ?, ?)",
                   (user_id, datetime.now().isoformat(timespec="minutes"), emotion,
                    excerpt[:100] if config.STORE_EXCERPTS else ""))


def recent_moods(user_id: str, limit: int = 10) -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT ts, emotion FROM moods WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                          (user_id, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]


def delete_user(user_id: str) -> int:
    """Erase everything stored about a user. Returns the number of rows deleted."""
    with connect() as db:
        n = db.execute("DELETE FROM moods WHERE user_id = ?", (user_id,)).rowcount
        n += db.execute("DELETE FROM memory WHERE user_id = ?", (user_id,)).rowcount
    return n
