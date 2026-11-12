"""SQLite 日报历史存储。仅此模块持有 SQL。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "daily_report.db"


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL UNIQUE,
                content     TEXT    NOT NULL,
                channels    TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_report(date: str, content: str, channels: list[str], db_path: str | Path | None = None) -> None:
    """同日期 upsert：覆盖为最新一份（proposal S10）。"""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO reports(date, content, channels) VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                content = excluded.content,
                channels = excluded.channels
            """,
            (date, content, ",".join(channels)),
        )
        conn.commit()
    finally:
        conn.close()


def list_history(db_path: str | Path | None = None) -> list[dict]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, date, channels, created_at FROM reports ORDER BY date DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
