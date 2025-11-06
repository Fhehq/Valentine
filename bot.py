import os

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.user_manager import UserManager
from app.handlers.generate_photo import register_photo_handlers
from app.handlers.admin_handler import register_admin_handlers
from app.handlers.profile import register_profile_handlers
from app.reset_limits import start_nightly_reset_scheduler
from app.utils.logger import setup_logging, get_logger
from config import BOT_TOKEN

setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))

logger = get_logger(__name__)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

user_manager = UserManager()

register_photo_handlers(dp, user_manager)
register_admin_handlers(dp, user_manager)
register_profile_handlers(dp, user_manager)

start_nightly_reset_scheduler(user_manager=user_manager, reset_time="00:00")


@dp.message(Command("start"))
async def main(message: types.Message):
    """Главное меню"""
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    user_id = int(message.chat.id)
    if await user_manager.is_new_user(user_id=user_id):
        await user_manager.add_user(user_id=user_id)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📷 Сгенерировать фото')],
            [KeyboardButton(text='🔍 Профиль')]
        ],
        resize_keyboard=True
    )
    
    if await user_manager.is_admin(user_id=user_id):
        keyboard.keyboard.append([KeyboardButton(text='⚙️ Админ меню')])

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

    await message.answer(
        text=text,
        reply_markup=keyboard
    )


async def main_async():
    """Основная асинхронная функция запуска бота"""
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {type(e).__name__}: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {type(e).__name__}: {e}", exc_info=True)
        logger.info("Переподключение к серверам Telegram...")
        asyncio.run(main_async())