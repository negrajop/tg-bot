import sqlite3
from datetime import date, datetime

from config import DB_PATH


REQUIRED_COLUMNS = {
    "user_id",
    "entry_date",
    "username",
    "value",
    "created_at",
    "updated_at",
}


def _connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _get_table_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _create_mood_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS mood (
            user_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            username TEXT NOT NULL,
            value INTEGER NOT NULL CHECK(value BETWEEN 1 AND 5),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, entry_date)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mood_username
        ON mood(username)
        """
    )
    connection.commit()


def _migrate_schema(connection):
    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    if "mood" not in tables:
        _create_mood_table(connection)
        return

    existing_columns = _get_table_columns(connection, "mood")
    if REQUIRED_COLUMNS.issubset(existing_columns):
        _create_mood_table(connection)
        return

    backup_name = f"mood_legacy_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    connection.execute(f"ALTER TABLE mood RENAME TO {backup_name}")
    _create_mood_table(connection)


def init_db():
    connection = _connect()
    try:
        _migrate_schema(connection)
    finally:
        connection.close()


def _normalize_entry_date(entry_date: str | date) -> str:
    if isinstance(entry_date, date):
        return entry_date.isoformat()

    return date.fromisoformat(entry_date).isoformat()


def _normalize_username(username: str | None, user_id: int) -> str:
    if username:
        return username.lstrip("@")

    return f"user_{user_id}"


def save_mood(user_id: int, username: str | None, entry_date: str | date, value: int):
    init_db()

    if value < 1 or value > 5:
        raise ValueError("Оценка настроения должна быть от 1 до 5.")

    normalized_date = _normalize_entry_date(entry_date)
    normalized_username = _normalize_username(username, user_id)
    now = datetime.now().isoformat()

    connection = _connect()
    try:
        connection.execute(
            """
            INSERT INTO mood (
                user_id,
                entry_date,
                username,
                value,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, entry_date) DO UPDATE SET
                username = excluded.username,
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                normalized_date,
                normalized_username,
                value,
                now,
                now,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def save_moods(user_id: int, username: str | None, entries: list[tuple[str, int]]):
    for entry_date, value in entries:
        save_mood(user_id, username, entry_date, value)


def get_user_moods(user_id: int, start: str = None, end: str = None):
    init_db()

    connection = _connect()
    try:
        query = """
            SELECT user_id, username, entry_date, value, created_at, updated_at
            FROM mood
            WHERE user_id = ?
        """
        params = [user_id]

        if start:
            query += " AND entry_date >= ?"
            params.append(date.fromisoformat(start).isoformat())

        if end:
            query += " AND entry_date <= ?"
            params.append(date.fromisoformat(end).isoformat())

        query += " ORDER BY entry_date"

        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_user_profile(user_id: int):
    init_db()

    connection = _connect()
    try:
        row = connection.execute(
            """
            SELECT user_id, username
            FROM mood
            WHERE user_id = ?
            ORDER BY entry_date DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        if not row:
            return None

        return dict(row)
    finally:
        connection.close()
