from io import BytesIO
from statistics import mean

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from datetime import datetime


def format_username(username: str | None, user_id: int | None = None) -> str:
    if username:
        if username.startswith("@") or " " in username:
            return username
        return f"@{username}"

    if user_id is not None:
        return f"user_{user_id}"

    return "unknown user"


def calculate_happiness_index(moods: list[dict], window: int = 7) -> int | None:
    if not moods:
        return None

    values = [item["value"] for item in moods[-window:]]
    return round(mean(values) * 20)


def build_happiness_series(moods: list[dict], window: int = 7) -> list[int]:
    values = [item["value"] for item in moods]
    series = []

    for index in range(len(values)):
        window_values = values[max(0, index - window + 1) : index + 1]
        series.append(round(mean(window_values) * 20))

    return series


def render_user_chart(
    moods: list[dict],
    username: str | None,
    user_id: int,
) -> BytesIO | None:
    if not moods:
        return None

    dates = [datetime.fromisoformat(item["entry_date"]) for item in moods]
    values = [item["value"] for item in moods]
    happiness_index = calculate_happiness_index(moods)
    happiness_series = build_happiness_series(moods)
    avg_value = mean(values)
    user_label = format_username(username, user_id)

    figure, axis_mood = plt.subplots(figsize=(12, 6))
    axis_index = axis_mood.twinx()

    bar_colors = ["#d1495b", "#edae49", "#66a182", "#4f772d", "#1a936f"]
    axis_mood.bar(
        dates,
        values,
        width=0.8,
        color=[bar_colors[value - 1] for value in values],
        alpha=0.85,
        label="Оценка за день",
    )
    axis_index.plot(
        dates,
        happiness_series,
        color="#0d3b66",
        linewidth=2.5,
        marker="o",
        markersize=4,
        label="Индекс счастья",
    )

    axis_mood.set_title(
        f"Настроение пользователя {user_label}\n"
        f"Текущий индекс счастья: {happiness_index}/100",
        fontsize=14,
        pad=16,
    )
    axis_mood.set_xlabel("Дата")
    axis_mood.set_ylabel("Оценка настроения", color="#333333")
    axis_index.set_ylabel("Индекс счастья", color="#0d3b66")
    axis_mood.set_ylim(0.5, 5.5)
    axis_index.set_ylim(0, 100)
    axis_mood.set_yticks([1, 2, 3, 4, 5])
    axis_index.set_yticks([0, 20, 40, 60, 80, 100])
    axis_mood.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    axis_mood.xaxis.set_major_locator(
        mdates.DayLocator(interval=max(1, len(dates) // 10))
    )
    axis_mood.grid(True, axis="y", linestyle="--", alpha=0.3)
    figure.autofmt_xdate()

    stats_text = (
        f"Записей: {len(moods)}\n"
        f"Средняя оценка: {avg_value:.2f}/5\n"
        f"Последняя дата: {moods[-1]['entry_date']}"
    )
    axis_mood.text(
        0.02,
        0.96,
        stats_text,
        transform=axis_mood.transAxes,
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )

    mood_handles, mood_labels = axis_mood.get_legend_handles_labels()
    index_handles, index_labels = axis_index.get_legend_handles_labels()
    axis_mood.legend(
        mood_handles + index_handles,
        mood_labels + index_labels,
        loc="upper right",
    )

    figure.tight_layout()

    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(figure)
    buffer.seek(0)
    return buffer
