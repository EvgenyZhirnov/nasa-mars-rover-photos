"""
Comment storage using SQLite.
Supports general site reviews and per-photo comments.
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

DB_PATH = config.DATA_DIR / "comments.db"


def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                page_type  TEXT    NOT NULL,
                item_id    TEXT,
                author     TEXT    NOT NULL,
                text       TEXT    NOT NULL,
                rating     INTEGER,
                created_at TEXT    NOT NULL
            )
        """)
        conn.commit()
    logger.info("Comments DB ready")


def add_comment(page_type: str, item_id: str | None,
                author: str, text: str, rating: int | None = None) -> int:
    """Insert a comment. Returns the new row id."""
    author = author.strip()[:80] or "Anonymous"
    text   = text.strip()[:2000]
    if rating is not None:
        rating = max(1, min(5, int(rating)))

    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO comments (page_type, item_id, author, text, rating, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (page_type, item_id, author, text, rating, datetime.now().isoformat(timespec='seconds'))
        )
        conn.commit()
        return cur.lastrowid


def get_comments(page_type: str, item_id: str | None = None) -> list[dict]:
    """Return comments, newest first."""
    with _connect() as conn:
        if item_id is not None:
            rows = conn.execute(
                "SELECT * FROM comments WHERE page_type=? AND item_id=? ORDER BY created_at DESC",
                (page_type, item_id)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM comments WHERE page_type=? ORDER BY created_at DESC",
                (page_type,)
            ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """Return aggregate stats for the status endpoint."""
    with _connect() as conn:
        total   = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        reviews = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE page_type='review'"
        ).fetchone()[0]
        photos  = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE page_type='photo'"
        ).fetchone()[0]
    return {"total": total, "reviews": reviews, "photo_comments": photos}
