import asyncio
import re
from datetime import date

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from charts import calculate_happiness_index, format_username, render_user_chart
from config import BOT_TOKEN
from db import get_user_moods, init_db, save_mood, save_moods

init_db()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

MOODS = {
    "Отлично": 5,
    "Хорошо": 4,
    "Нормально": 3,
    "Плохо": 2,
    "Ужасно": 1,
}
EDIT_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})\s*[:=]?\s*([1-5])")


def get_keyboard():
    keyboard = InlineKeyboardBuilder()
    for text, value in MOODS.items():
        keyboard.add(
            InlineKeyboardButton(text=text, callback_data=f"mood:{value}")
        )
    keyboard.adjust(1)
    return keyboard.as_markup()


def format_index(index: int | None) -> str:
    if index is None:
        return "пока нет данных"

    return f"{index}/100"


def parse_edit_entries(text: str) -> list[tuple[str, int]]:
    entries = {}

    for entry_date, value in EDIT_PATTERN.findall(text):
        date.fromisoformat(entry_date)
        entries[entry_date] = int(value)

    return sorted(entries.items())


async def send_chart(message: Message, user_id: int, username: str | None):
    moods = get_user_moods(user_id)
    chart = render_user_chart(moods, username, user_id)

    if not chart:
        return

    photo = BufferedInputFile(chart.getvalue(), filename="mood_chart.png")
    index = calculate_happiness_index(moods)
    await message.answer_photo(
        photo=photo,
        caption=(
            f"График пользователя {format_username(username, user_id)}\n"
            f"Индекс счастья: {format_index(index)}"
        ),
    )


@dp.message(Command("start"))
async def start(message: Message):
    user = message.from_user
    moods = get_user_moods(user.id)
    index = calculate_happiness_index(moods)
    username = user.username

    await message.answer(
        (
            f"Привет, {format_username(username, user.id)}!\n"
            f"Текущий индекс счастья: {format_index(index)}\n\n"
            "Выбери оценку за сегодня или отредактируй прошлые дни командой:\n"
            "/edit 2026-03-20 4 2026-03-21 5"
        ),
        reply_markup=get_keyboard(),
    )
    await send_chart(message, user.id, username)


@dp.message(Command("edit"))
async def edit_moods(message: Message):
    raw_entries = message.text.partition(" ")[2]

    if not raw_entries.strip():
        await message.answer(
            "Укажи пары дата-оценка. Пример:\n"
            "/edit 2026-03-20 4 2026-03-21 5"
        )
        return

    try:
        entries = parse_edit_entries(raw_entries)
    except ValueError:
        await message.answer(
            "Не удалось разобрать даты. Используй формат YYYY-MM-DD 1..5."
        )
        return

    if not entries:
        await message.answer(
            "Не нашёл ни одной пары дата-оценка. Пример:\n"
            "/edit 2026-03-20 4 2026-03-21 5"
        )
        return

    user = message.from_user
    save_moods(user.id, user.username, entries)

    moods = get_user_moods(user.id)
    index = calculate_happiness_index(moods)
    updated_lines = [f"{entry_date}: {value}/5" for entry_date, value in entries]

    await message.answer(
        "Обновил записи:\n"
        + "\n".join(updated_lines)
        + f"\n\nТекущий индекс счастья: {format_index(index)}"
    )
    await send_chart(message, user.id, user.username)


@dp.callback_query(F.data.startswith("mood:"))
async def handle_mood(callback: CallbackQuery):
    mood_value = int(callback.data.split(":", maxsplit=1)[1])
    user = callback.from_user
    today = date.today()

    save_mood(user.id, user.username, today, mood_value)
    moods = get_user_moods(user.id)
    index = calculate_happiness_index(moods)

    await callback.answer("Сохранено")
    await callback.message.answer(
        f"Записал настроение за {today.isoformat()}: {mood_value}/5\n"
        f"Текущий индекс счастья: {format_index(index)}"
    )


async def main():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
