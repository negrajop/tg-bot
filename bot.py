import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN
from db import insert_mood, init_db

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


def get_keyboard():
    keyboard = InlineKeyboardBuilder()
    for text in MOODS:
        keyboard.add(InlineKeyboardButton(text=text, callback_data=text))
    keyboard.adjust(1)
    return keyboard.as_markup()


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Как ты себя чувствуешь?",
        reply_markup=get_keyboard(),
    )


@dp.callback_query(F.data.in_(MOODS))
async def handle_mood(callback: CallbackQuery):
    mood_value = MOODS[callback.data]
    insert_mood(mood_value)

    await callback.answer("Сохранено")
    await callback.message.answer("Данные записаны")


async def main():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
