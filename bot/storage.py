"""Bot foydalanuvchilari uchun oddiy SQLite saqlash:
bildirishnoma sozlamalari va saqlangan maqolalar."""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("BOT_DB_PATH", Path(__file__).parent / "bot.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "  chat_id INTEGER PRIMARY KEY,"
        "  notifications INTEGER DEFAULT 1,"
        "  language TEXT DEFAULT 'uz'"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS saved ("
        "  chat_id INTEGER,"
        "  article_slug TEXT,"
        "  article_title TEXT,"
        "  PRIMARY KEY (chat_id, article_slug)"
        ")"
    )
    return conn


def ensure_user(chat_id: int):
    with _connect() as conn:
        conn.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))


def toggle_notifications(chat_id: int) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT notifications FROM users WHERE chat_id=?", (chat_id,)).fetchone()
        new_value = 0 if (row and row[0]) else 1
        conn.execute(
            "INSERT INTO users (chat_id, notifications) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET notifications=?",
            (chat_id, new_value, new_value),
        )
        return bool(new_value)


def save_article(chat_id: int, slug: str, title: str):
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO saved (chat_id, article_slug, article_title) VALUES (?, ?, ?)",
            (chat_id, slug, title),
        )


def get_saved(chat_id: int) -> list[tuple[str, str]]:
    with _connect() as conn:
        return conn.execute(
            "SELECT article_slug, article_title FROM saved WHERE chat_id=?", (chat_id,)
        ).fetchall()


def notification_subscribers() -> list[int]:
    with _connect() as conn:
        return [row[0] for row in conn.execute("SELECT chat_id FROM users WHERE notifications=1")]
