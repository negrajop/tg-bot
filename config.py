import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "database.db")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не задана")
