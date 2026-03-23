import sqlite3
from config import DB_PATH
from datetime import datetime

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mood (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        value INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_mood(value: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO mood (value, created_at) VALUES (?, ?)",
        (value, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_moods(start=None, end=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT value, created_at FROM mood"
    params = []

    if start and end:
        query += " WHERE created_at BETWEEN ? AND ?"
        params.extend([start, end])

    query += " ORDER BY created_at"

    cursor.execute(query, params)
    data = cursor.fetchall()

    conn.close()
    return data