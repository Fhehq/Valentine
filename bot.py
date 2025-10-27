import time
import requests
from urllib3.exceptions import ProtocolError
import os

from telebot import types

from config import bot
from app.user_manager import UserManager

from app.handlers.generate_photo import register_photo_handlers
from app.handlers.admin_handler import register_admin_handlers
from app.reset_limits import start_nightly_reset_scheduler
print("Бот запущен")

user_manager = UserManager()

register_photo_handlers(bot)
register_admin_handlers(bot)
start_nightly_reset_scheduler(user_manager=user_manager, reset_time="00:00")

@bot.message_handler(commands=["start"])
def main(message):
    print("Получена команда - Start")
    "Главное меню"""
    user_id = int(message.chat.id)
    if user_manager.is_new_user(user_id=user_id):
        user_manager.add_user(user_id=user_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    get_photo = types.KeyboardButton('📷 Сгенерировать фото')
    keyboard.add(get_photo)
    if user_manager.is_admin(user_id=user_id):
        admin_menu = types.KeyboardButton('⚙️ Админ меню')
        keyboard.add(admin_menu)

    text = (
        "✨ *Добро пожаловать!* ✨\n\n"
        "Здесь вы можете превратить вашу переписку в *креативные фотографии* необычной формы! 🎨\n\n"
        "```🔒конфиденциальность:\n"
        "• Бот не сохраняет ваши фото и сообщения\n"
        "• Все обработки происходят в реальном времени\n"
        "• Ваши данные в полной безопасности\n\n"
        "📂 Открытый исходный код:\n"
        "Весь проект полностью прозрачен — вы можете ознакомиться с кодом и убедиться в безопасности (Ссылка в описание бота). 🔍\n\n"
        "🚀 Начните творить прямо сейчас!```"
    )

    bot.send_message(
        message.chat.id,
        text=text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

while True:
    try:
        bot.polling(
            none_stop=True,
            timeout=10,
            long_polling_timeout=10,
            interval=2
        )

    except (requests.exceptions.ConnectionError, ProtocolError, TimeoutError):
        print("Переподключение к серверам Telegram...")
        time.sleep(15)
        continue

    except Exception as e:
        print(f"Ошибка: {type(e).__name__}: {e}")
        time.sleep(15)
        continue