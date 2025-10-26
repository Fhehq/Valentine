from telebot import types
from app.user_manager import UserManager

user_manager = UserManager()

def register_admin_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == '⚙️ Админ меню')
    def adm_panel(message):
        markup = types.InlineKeyboardMarkup(row_width=3)
        spam = types.InlineKeyboardButton("✉️ Рассылка", callback_data="spam") 
        add_admin = types.InlineKeyboardButton("✅ Добавить админа", callback_data="add_admin") 
        del_admin = types.InlineKeyboardButton("❌ Удалить админа", callback_data="del_admin") 
        users = types.InlineKeyboardButton("👫 Кол-во Юзеров", callback_data="users")
        markup.add(spam, users)
        markup.add(add_admin, del_admin)
        bot.send_message(message.chat.id, "👋🏿 Добро пожаловать в Админ меню", reply_markup=markup)

    
    @bot.callback_query_handler(func=lambda call: call.data == "users")
    def get_all_users(call):
        user_id = call.from_user.id
        if not user_manager.is_admin(user_id):
            bot.send_message(call.message.chat.id, "❌ У вас нет доступа к этой команде")
            return
        all_users = len(user_manager.get_users())
        bot.send_message(call.message.chat.id, f"📊 Кол-во юзеров - {all_users}")
        
    @bot.callback_query_handler(func=lambda call: call.data == "spam")
    
    def start_broadcast(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if not user_manager.is_admin(user_id):
            bot.send_message(chat_id, "❌ У вас нет доступа к этой команде")
            return

        msg = bot.send_message(chat_id, "✏️ Введите текст для рассылки:")
        bot.register_next_step_handler(msg, send_broadcast)

    def send_broadcast(message):
        text_to_send = message.text
        status_msg = bot.send_message(message.chat.id, "🚀 Запуск рассылки...")

        users = user_manager.get_users()

        for uid in users:
            try:
                bot.send_message(uid, text_to_send)
            except Exception as e:
                print(f"Не удалось отправить пользователю {uid}: {e}")

        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение о рассылке: {e}")

        bot.send_message(message.chat.id, f"✅ Рассылка завершена для {len(users)} пользователей")

    @bot.callback_query_handler(func=lambda call: call.data in ["add_admin", "del_admin"])
    def add_del_admin(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if not user_manager.is_admin(user_id):
            bot.send_message(chat_id, "❌ У вас нет доступа к этой команде")
            return

        action = call.data
        msg = bot.send_message(chat_id, "✏️ Введите ID пользователя (или напишите 'отмена'):")
        bot.register_next_step_handler(msg, process_admin_id_step, action)

    def process_admin_id_step(message, action):
        text = (message.text or "").strip()
        chat_id = message.chat.id

        if text.lower() in ("отмена", "cancel"):
            bot.send_message(chat_id, "❌ Операция отменена")
            return

        try:
            target_id = int(text)
        except ValueError:
            bot.send_message(chat_id, "❌ Неверный формат ID. Введите числовой ID.")
            return

        if not user_manager.is_admin(message.from_user.id):
            bot.send_message(chat_id, "❌ У вас больше нет доступа к этой команде")
            return

        try:
            if action == "add_admin":
                user_manager.add_admin(target_id)
                bot.send_message(chat_id, f"✅ Пользователь {target_id} теперь админ")
            elif action == "del_admin":
                user_manager.remove_admin(target_id)
                bot.send_message(chat_id, f"✅ Права админа у пользователя {target_id} сняты")
            else:
                bot.send_message(chat_id, "❌ Неизвестное действие")
        except Exception as e:
            print(f"Ошибка при изменении прав: {e}")
            bot.send_message(chat_id, "❌ Произошла ошибка при обновлении БД")