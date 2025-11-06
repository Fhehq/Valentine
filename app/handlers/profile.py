from aiogram import Dispatcher, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
import os
import sys
import asyncio
sys.path.append(os.getcwd())
from app.decoder import extract_zip
from app.user_manager import UserManager
from app.utils.logger import get_logger

logger = get_logger(__name__)



def register_profile_handlers(dp: Dispatcher, user_manager: UserManager):
    @dp.message(F.text == '🔍 Профиль')
    async def choose_pattern(message: types.Message):
        user_id = message.chat.id
        
        logger.info(f"Пользователь {user_id} запросил профиль")
        
        user_name = message.chat.username
        balance = await  user_manager.get_balance(user_id)
        limits = await  user_manager.get_limits(user_id, counts=True)
        text = (f"*👨🏻Профиль пользователя:* @{user_name} (id: {user_id})\n"
                f"*💵 Баланс:* {balance} руб.\n"
                f"*🔓 Лимиты:* {limits}/3\n"
                )
        
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup"),
            ],
        ]) 
        
        await message.answer(text, reply_markup=markup)
