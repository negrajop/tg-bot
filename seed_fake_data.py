import argparse
import random
from datetime import date, timedelta

from db import init_db, save_moods


START_DATE = date(2026, 3, 1)


def generate_fake_rows(start_date: date, end_date: date) -> list[tuple[str, int]]:
    rng = random.Random(20260301)
    current_day = start_date
    baseline = 4
    rows = []

    while current_day <= end_date:
        baseline = min(5, max(1, baseline + rng.choice([-1, 0, 0, 1])))
        value = min(5, max(1, baseline + rng.choice([-1, 0, 0, 1])))
        rows.append((current_day.isoformat(), value))
        current_day += timedelta(days=1)

    return rows


def parse_args():
    parser = argparse.ArgumentParser(
        description="Заполняет БД фейковыми пользовательскими данными о настроении."
    )
    parser.add_argument("--user-id", type=int, default=1, help="Telegram user id")
    parser.add_argument(
        "--username",
        default="demo_user",
        help="Username пользователя для тестовых данных",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    end_date = date.today()

    if end_date < START_DATE:
        raise ValueError(
            f"Текущая дата {end_date.isoformat()} раньше даты старта {START_DATE.isoformat()}."
        )

    init_db()
    rows = generate_fake_rows(START_DATE, end_date)
    save_moods(args.user_id, args.username, rows)

    print(
        f"Добавлено или обновлено {len(rows)} записей для "
        f"@{args.username} ({args.user_id}) за период "
        f"{START_DATE.isoformat()} - {end_date.isoformat()}."
    )


if __name__ == "__main__":
    main()
