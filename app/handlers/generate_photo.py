from aiogram import Dispatcher, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
import os
import sys
import asyncio
sys.path.append(os.getcwd())
import get_photo
from app.decoder import extract_zip
from app.user_manager import UserManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PhotoGenerationStates(StatesGroup):
    waiting_for_zip = State()


def register_photo_handlers(dp: Dispatcher, user_manager: UserManager):
    @dp.message(F.text == '📷 Сгенерировать фото')
    async def choose_pattern(message: types.Message):
        user_id = message.chat.id
        logger.info(f"Пользователь {user_id} запросил генерацию фото")
        if await user_manager.get_limits(user_id=user_id):
            patterns_dir = 'patterns'
            pattern_files = [f for f in os.listdir(patterns_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

            if not pattern_files:
                await message.answer("⚠️ Паттерны не найдены, обратитесь в поддержку.")
                return
            
            msg_text = "✨ Выберите нужный паттерн\n\n"
            for idx, pattern in enumerate(pattern_files, start=1):
                msg_text += f"{idx}: {os.path.splitext(pattern)[0]}\n"

            buttons = []
            for i in range(0, len(pattern_files), 3):
                row = [
                    types.InlineKeyboardButton(text=str(j+1), callback_data=f"pattern_{j}")
                    for j in range(i, min(i+3, len(pattern_files)))
                ]
                buttons.append(row)
            
            markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

            await message.answer(msg_text, reply_markup=markup)
        else:
            await message.answer("😢 У вас закончились лимиты, приходите завтра")

    @dp.callback_query(F.data.startswith('pattern_'))
    async def handle_pattern_choice(callback: types.CallbackQuery, state: FSMContext):
        index = int(callback.data.split('_')[1])
        patterns_dir = 'patterns'
        pattern_files = [f for f in os.listdir(patterns_dir)]
        user_id = callback.from_user.id
        
        if await user_manager.get_limits(user_id=user_id):
            if index >= len(pattern_files):
                await callback.answer("❌ Ошибка выбора", show_alert=True)
                return

            selected_pattern = pattern_files[index]
            await callback.answer(f"✅ Вы выбрали: {selected_pattern}")

            await state.update_data(selected_pattern=selected_pattern)
            await callback.message.edit_text(
                f"📁 Теперь отправь ZIP-архив с перепиской (только один файл формата json)\n"
                f"Ссылка как получить историю чата и сделать ZIP архив - [тут](https://t.me/valentine_guide)\n\n"
                f"Паттерн: *{os.path.splitext(selected_pattern)[0]}*",
                parse_mode="Markdown"
            )
            await state.set_state(PhotoGenerationStates.waiting_for_zip)
        else:
            await callback.answer("😢 У вас закончились лимиты, приходите завтра", show_alert=True)

    @dp.message(StateFilter(PhotoGenerationStates.waiting_for_zip))
    async def handle_zip_upload(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        
        if not await user_manager.get_limits(user_id=user_id):
            await message.answer("😢 У вас закончились лимиты, приходите завтра")
            await state.clear()
            return

        if not message.document:
            await message.answer("❌ Отправь именно ZIP-архив, а не текст. Попробуй еще раз:")
            return

        if not message.document.file_name.lower().endswith('.zip'):
            await message.answer("⚠️ Нужен файл в формате .zip. Попробуй еще раз:")
            return

        data = await state.get_data()
        selected_pattern = data.get("selected_pattern")
        
        if not selected_pattern:
            await message.answer("❌ Ошибка: паттерн не найден. Начните заново.")
            await state.clear()
            return

        try:
            file = await message.bot.get_file(message.document.file_id)
            downloaded_file = await message.bot.download_file(file.file_path)

            temp_dir = 'temp'
            os.makedirs(temp_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, f"{user_id}.zip")

            file_data = downloaded_file.read()
            def save_file(path, data):
                with open(path, 'wb') as f:
                    f.write(data)
            await asyncio.to_thread(save_file, zip_path, file_data)

            json_path = await asyncio.to_thread(extract_zip, zip_path)
            if not json_path or not os.path.exists(json_path):
                await message.answer("❌ В архиве должен быть только один файл — result.json.")
                if os.path.exists(zip_path):
                    await asyncio.to_thread(os.remove, zip_path)
                await state.clear()
                return
            
            status_msg = await message.answer("🧬 Генерация фото...")
            logger.info(f"Начало генерации фото для пользователя {user_id}, паттерн: {selected_pattern}")
            
            if os.path.exists(zip_path):
                await asyncio.to_thread(os.remove, zip_path)

            photo_path = None
            try:
                photo_path, first_msg = await asyncio.to_thread(
                    get_photo.main,
                    user_id=user_id,
                    pattern=os.path.splitext(selected_pattern)[0],
                    file=json_path
                )

                if photo_path and os.path.exists(photo_path):
                    document = FSInputFile(photo_path)
                    await message.bot.send_document(
                        chat_id=user_id,
                        document=document,
                        caption=f"🎉 Облако слов сгенерировано успешно!\n\n✨ Первое сообщение:\n'{first_msg}'"
                    )
                    await user_manager.increment_limits(user_id=user_id)
                    logger.info(f"Фото успешно сгенерировано и отправлено пользователю {user_id}")
                else:
                    await message.answer("❌ Ошибка: не удалось создать фото")

            except Exception as e:
                logger.error(f"Ошибка при генерации фото для пользователя {user_id}: {e}", exc_info=True)
                await message.answer(f"❌ Ошибка при генерации: {e}")

            finally:
                try:
                    await message.bot.delete_message(user_id, status_msg.message_id)
                except Exception as e:
                    logger.warning(f"Не удалось удалить сообщение о генерации для пользователя {user_id}: {e}")

                if os.path.exists(json_path):
                    await asyncio.to_thread(os.remove, json_path)
                if photo_path and os.path.exists(photo_path):
                    await asyncio.to_thread(os.remove, photo_path)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Ошибка при обработке файла для пользователя {user_id}: {e}", exc_info=True)
            await message.answer(f"❌ Произошла ошибка при обработке файла: {e}")
            await state.clear()