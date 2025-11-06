from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Установите переменную окружения BOT_TOKEN или создайте .env файл с BOT_TOKEN=ваш_токен")