import argparse
import os
import random
import sqlite3
from datetime import date, datetime, time, timedelta

from dotenv import load_dotenv


START_DATE = date(2026, 3, 1)


def get_db_path() -> str:
    load_dotenv()
    return os.getenv("DB_PATH", "database.db")


def init_db(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mood (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value INTEGER,
            created_at TEXT
        )
        """
    )
    connection.commit()


def generate_fake_rows(start_date: date, end_date: date) -> list[tuple[int, str]]:
    rng = random.Random(20260301)
    current_day = start_date
    baseline = 4
    rows: list[tuple[int, str]] = []

    while current_day <= end_date:
        entries_count = rng.randint(1, 3)
        baseline = min(5, max(1, baseline + rng.choice([-1, 0, 0, 1])))

        for _ in range(entries_count):
            value = min(5, max(1, baseline + rng.choice([-1, 0, 0, 1])))
            hour = rng.randint(9, 22)
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            created_at = datetime.combine(
                current_day,
                time(hour=hour, minute=minute, second=second),
            ).isoformat()
            rows.append((value, created_at))

        current_day += timedelta(days=1)

    rows.sort(key=lambda row: row[1])
    return rows


def clear_range(
    connection: sqlite3.Connection,
    start_date: date,
    end_date: date,
) -> None:
    start_dt = datetime.combine(start_date, time.min).isoformat()
    end_dt = datetime.combine(end_date, time.max).isoformat()
    connection.execute(
        "DELETE FROM mood WHERE created_at BETWEEN ? AND ?",
        (start_dt, end_dt),
    )
    connection.commit()


def insert_rows(connection: sqlite3.Connection, rows: list[tuple[int, str]]) -> None:
    connection.executemany(
        "INSERT INTO mood (value, created_at) VALUES (?, ?)",
        rows,
    )
    connection.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Заполняет БД фейковыми данными о настроении."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Удалить существующие записи в диапазоне перед заполнением.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = get_db_path()
    end_date = date.today()

    if end_date < START_DATE:
        raise ValueError(
            f"Текущая дата {end_date.isoformat()} раньше даты старта {START_DATE.isoformat()}."
        )

    rows = generate_fake_rows(START_DATE, end_date)

    connection = sqlite3.connect(db_path)
    try:
        init_db(connection)

        if args.reset:
            clear_range(connection, START_DATE, end_date)

        insert_rows(connection, rows)
    finally:
        connection.close()

    print(
        f"Добавлено {len(rows)} записей в {db_path} "
        f"за период {START_DATE.isoformat()} - {end_date.isoformat()}."
    )


if __name__ == "__main__":
    main()
