import json
import re
from datetime import date

from vkbottle import Bot, Keyboard, KeyboardButtonColor, PhotoMessageUploader, Text
from vkbottle.bot import Message

from charts import calculate_happiness_index, format_username, render_user_chart
from config import VK_BOT_TOKEN
from db import get_user_moods, init_db, save_mood, save_moods

init_db()

bot = Bot(token=VK_BOT_TOKEN)
photo_uploader = PhotoMessageUploader(bot.api)

MOODS = {
    "Отлично": 5,
    "Хорошо": 4,
    "Нормально": 3,
    "Плохо": 2,
    "Ужасно": 1,
}
MOOD_TEXT_TO_VALUE = {label.lower(): value for label, value in MOODS.items()}
MOOD_BUTTON_COLORS = {
    5: KeyboardButtonColor.POSITIVE,
    4: KeyboardButtonColor.POSITIVE,
    3: KeyboardButtonColor.PRIMARY,
    2: KeyboardButtonColor.NEGATIVE,
    1: KeyboardButtonColor.NEGATIVE,
}
START_COMMANDS = {"/start", "start", "начать"}
HELP_COMMANDS = {"/help", "help", "помощь"}
EDIT_PREFIXES = ("/edit", "edit")
EDIT_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})\s*[:=]?\s*([1-5])")


def get_keyboard() -> str:
    keyboard = Keyboard(one_time=False, inline=False)

    for index, (text, value) in enumerate(MOODS.items()):
        keyboard.add(
            Text(text, payload={"command": "mood", "value": value}),
            color=MOOD_BUTTON_COLORS[value],
        )
        if index < len(MOODS) - 1:
            keyboard.row()

    return keyboard.get_json()


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


def parse_payload(message: Message) -> dict:
    payload = message.payload

    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str):
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return {}

        if isinstance(decoded, dict):
            return decoded

    return {}


def extract_command_args(text: str) -> str:
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        return ""
    return parts[1]


def build_help_text() -> str:
    return (
        "Выбери оценку за сегодня кнопками ниже или отправь её текстом.\n"
        "Для редактирования прошлых дней используй команду:\n"
        "/edit 2026-03-20 4 2026-03-21 5"
    )


async def resolve_username(user_id: int) -> str | None:
    users = await bot.api.users.get(user_ids=user_id, fields=["screen_name"])
    if not users:
        return None

    user = users[0]
    screen_name = getattr(user, "screen_name", None)
    if screen_name:
        return screen_name

    first_name = getattr(user, "first_name", None)
    last_name = getattr(user, "last_name", None)
    full_name = " ".join(part for part in (first_name, last_name) if part).strip()
    return full_name or None


async def send_chart(message: Message, user_id: int, username: str | None):
    moods = get_user_moods(user_id)
    chart = render_user_chart(moods, username, user_id)

    if not chart:
        return

    attachment = await photo_uploader.upload(
        file_source=chart.getvalue(),
        peer_id=message.peer_id,
    )
    index = calculate_happiness_index(moods)

    await message.answer(
        message=(
            f"График пользователя {format_username(username, user_id)}\n"
            f"Индекс счастья: {format_index(index)}"
        ),
        attachment=attachment,
    )


async def handle_start(message: Message):
    user_id = message.from_id
    if user_id is None:
        return

    username = await resolve_username(user_id)
    moods = get_user_moods(user_id)
    index = calculate_happiness_index(moods)

    await message.answer(
        message=(
            f"Привет, {format_username(username, user_id)}!\n"
            f"Текущий индекс счастья: {format_index(index)}\n\n"
            f"{build_help_text()}"
        ),
        keyboard=get_keyboard(),
    )
    await send_chart(message, user_id, username)


async def handle_edit(message: Message):
    raw_entries = extract_command_args(message.text or "")

    if not raw_entries.strip():
        await message.answer(message=build_help_text(), keyboard=get_keyboard())
        return

    try:
        entries = parse_edit_entries(raw_entries)
    except ValueError:
        await message.answer(
            message="Не удалось разобрать даты. Используй формат YYYY-MM-DD 1..5."
        )
        return

    if not entries:
        await message.answer(
            message=(
                "Не нашёл ни одной пары дата-оценка. Пример:\n"
                "/edit 2026-03-20 4 2026-03-21 5"
            )
        )
        return

    user_id = message.from_id
    if user_id is None:
        return

    username = await resolve_username(user_id)
    save_moods(user_id, username, entries)

    moods = get_user_moods(user_id)
    index = calculate_happiness_index(moods)
    updated_lines = [f"{entry_date}: {value}/5" for entry_date, value in entries]

    await message.answer(
        message=(
            "Обновил записи:\n"
            + "\n".join(updated_lines)
            + f"\n\nТекущий индекс счастья: {format_index(index)}"
        ),
        keyboard=get_keyboard(),
    )
    await send_chart(message, user_id, username)


async def handle_mood_value(message: Message, mood_value: int):
    user_id = message.from_id
    if user_id is None:
        return

    username = await resolve_username(user_id)
    today = date.today()

    save_mood(user_id, username, today, mood_value)
    moods = get_user_moods(user_id)
    index = calculate_happiness_index(moods)

    await message.answer(
        message=(
            f"Записал настроение за {today.isoformat()}: {mood_value}/5\n"
            f"Текущий индекс счастья: {format_index(index)}"
        ),
        keyboard=get_keyboard(),
    )


@bot.on.message()
async def handle_message(message: Message):
    payload = parse_payload(message)
    if payload.get("command") == "mood":
        mood_value = payload.get("value")
        if isinstance(mood_value, str) and mood_value.isdigit():
            mood_value = int(mood_value)
        if isinstance(mood_value, int) and 1 <= mood_value <= 5:
            await handle_mood_value(message, mood_value)
        return

    text = (message.text or "").strip()
    if not text:
        return

    normalized = text.lower()
    if normalized in START_COMMANDS or normalized in HELP_COMMANDS:
        await handle_start(message)
        return

    if normalized == "/edit" or normalized == "edit":
        await handle_edit(message)
        return

    if any(normalized.startswith(f"{prefix} ") for prefix in EDIT_PREFIXES):
        await handle_edit(message)
        return

    mood_value = MOOD_TEXT_TO_VALUE.get(normalized)
    if mood_value is not None:
        await handle_mood_value(message, mood_value)


if __name__ == "__main__":
    bot.run_forever()
