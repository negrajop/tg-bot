import argparse
from pathlib import Path

from charts import calculate_happiness_index, render_user_chart
from db import get_user_moods, get_user_profile, init_db


def parse_args():
    parser = argparse.ArgumentParser(
        description="Строит график настроения конкретного пользователя."
    )
    parser.add_argument("--user-id", type=int, required=True, help="Telegram user id")
    parser.add_argument(
        "--output",
        default="mood_chart.png",
        help="Путь для сохранения графика",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    init_db()
    moods = get_user_moods(args.user_id)

    if not moods:
        raise ValueError("По этому пользователю пока нет данных.")

    profile = get_user_profile(args.user_id)
    username = profile["username"] if profile else None
    happiness_index = calculate_happiness_index(moods)

    chart = render_user_chart(
        moods,
        username,
        args.user_id,
    )

    output_path = Path(args.output)
    output_path.write_bytes(chart.getvalue())

    print(
        f"График сохранён в {output_path}. "
        f"Индекс счастья: {happiness_index}/100."
    )


if __name__ == "__main__":
    main()
