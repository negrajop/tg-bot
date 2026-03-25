import os

from dotenv import load_dotenv

load_dotenv()

VK_BOT_TOKEN = os.getenv("VK_BOT_TOKEN") or os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "database.db")

if not VK_BOT_TOKEN:
    raise ValueError("Переменная окружения VK_BOT_TOKEN не задана")
