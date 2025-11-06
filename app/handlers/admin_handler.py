from aiogram import Dispatcher, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from app.user_manager import UserManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_admin_id = State()


def register_admin_handlers(dp: Dispatcher, user_manager: UserManager):
    @dp.message(F.text == '⚙️ Админ меню')
    async def adm_panel(message: types.Message):
        user_id = message.from_user.id
        if not await user_manager.is_admin(user_id):
            await message.answer("❌ У вас нет доступа к этой команде")
            return

        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✉️ Рассылка", callback_data="spam"),
                types.InlineKeyboardButton(text="👫 Кол-во Юзеров", callback_data="users")
            ],
            [
                types.InlineKeyboardButton(text="✅ Добавить админа", callback_data="add_admin"),
                types.InlineKeyboardButton(text="❌ Удалить админа", callback_data="del_admin")
            ]
        ])
        await message.answer("👋🏿 Добро пожаловать в Админ меню", reply_markup=markup)

    @dp.callback_query(F.data == "users")
    async def get_all_users(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if not await user_manager.is_admin(user_id):
            await callback.answer("❌ У вас нет доступа к этой команде", show_alert=True)
            return
        
        all_users = len(await user_manager.get_users())
        await callback.message.edit_text(f"📊 Кол-во юзеров - {all_users}")
        await callback.answer()

    @dp.callback_query(F.data == "spam")
    async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if not await user_manager.is_admin(user_id):
            await callback.answer("❌ У вас нет доступа к этой команде", show_alert=True)
            return

        await callback.message.edit_text("✏️ Введите текст для рассылки:")
        await state.set_state(AdminStates.waiting_for_broadcast_text)
        await callback.answer()

    @dp.message(StateFilter(AdminStates.waiting_for_broadcast_text))
    async def send_broadcast(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if not await user_manager.is_admin(user_id):
            await message.answer("❌ У вас нет доступа к этой команде")
            await state.clear()
            return

        text_to_send = message.text
        
        status_msg = await message.answer("🚀 Запуск рассылки...")

        users = await user_manager.get_users()
        total_users = len(users)
        logger.info(f"Начало рассылки от пользователя {user_id}. Получателей: {total_users}")
        
        success_count = 0
        batch_size = 20
        delay_between_batches = 0.05
        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            
            async def send_to_user(user_id):
                try:
                    await message.bot.send_message(user_id, text_to_send)
                    return (user_id, True, None)
                except Exception as e:
                    return (user_id, False, e)
            
            tasks = [send_to_user(uid) for uid in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Ошибка при отправке: {result}")
                else:
                    uid, success, error = result
                    if success:
                        success_count += 1
                    else:
                        logger.warning(f"Не удалось отправить пользователю {uid}: {error}")
            
            if i + batch_size < total_users:
                await asyncio.sleep(delay_between_batches)
            
            if (i + batch_size) % 100 == 0 or i + batch_size >= total_users:
                try:
                    await status_msg.edit_text(
                        f"🚀 Рассылка в процессе...\n"
                        f"Отправлено: {success_count} из {total_users}"
                    )
                except:
                    pass

        try:
            await message.bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение о рассылке: {e}")

        logger.info(f"Рассылка завершена. Успешно отправлено: {success_count} из {total_users}")
        await message.answer(f"✅ Рассылка завершена для {success_count} из {total_users} пользователей")
        await state.clear()

    @dp.callback_query(F.data.in_(["add_admin", "del_admin"]))
    async def add_del_admin(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if not await user_manager.is_admin(user_id):
            await callback.answer("❌ У вас нет доступа к этой команде", show_alert=True)
            return

        action = callback.data
        await state.update_data(action=action)
        await callback.message.edit_text("✏️ Введите ID пользователя (или напишите 'отмена'):")
        await state.set_state(AdminStates.waiting_for_admin_id)
        await callback.answer()

    @dp.message(StateFilter(AdminStates.waiting_for_admin_id))
    async def process_admin_id_step(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        if not await user_manager.is_admin(user_id):
            await message.answer("❌ У вас больше нет доступа к этой команде")
            await state.clear()
            return

        text = (message.text or "").strip()
        data = await state.get_data()
        action = data.get("action")

        if text.lower() in ("отмена", "cancel"):
            await message.answer("❌ Операция отменена")
            await state.clear()
            return

        try:
            target_id = int(text)
        except ValueError:
            await message.answer("❌ Неверный формат ID. Введите числовой ID.")
            return

        try:
            if action == "add_admin":
                await user_manager.add_admin(target_id)
                await message.answer(f"✅ Пользователь {target_id} теперь админ")
            elif action == "del_admin":
                await user_manager.remove_admin(target_id)
                await message.answer(f"✅ Права админа у пользователя {target_id} сняты")
            else:
                await message.answer("❌ Неизвестное действие")
        except Exception as e:
            logger.error(f"Ошибка при изменении прав для пользователя {target_id}: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при обновлении БД")
        finally:
            await state.clear()