from telebot import types
import os
import sys

sys.path.append(os.getcwd())
import get_photo

def register_photo_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == '📷 Сгенерировать фото')
    def choose_pattern(message):
        patterns_dir = 'patterns'
        pattern_files = [f for f in os.listdir(patterns_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not pattern_files:
            bot.send_message(message.chat.id, "⚠️ Паттерны не найдены, обратитесь в поддержку.")
            return
        msg_text = "✨ Выберите нужный паттерн\n\n"
        
        for idx, pattern in enumerate(pattern_files, start=1):
            msg_text += f"{idx}: {pattern[:-3]}\n"

        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(str(i), callback_data=f"pattern_{i-1}") 
                   for i in range(1, len(pattern_files)+1)]
        markup.add(*buttons)

        bot.send_message(message.chat.id, msg_text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('pattern_'))
    def handle_pattern_choice(call):
        
        status_msg = bot.send_message(call.from_user.id, "🧬 Генерация фото...")
        index = int(call.data.split('_')[1])
        patterns_dir = 'patterns'
        pattern_files = [f for f in os.listdir(patterns_dir)]
        user_id = call.from_user.id
        
        if index >= len(pattern_files):
            bot.answer_callback_query(call.id, "❌ Ошибка выбора")
            return

        selected_pattern = pattern_files[index]
        bot.answer_callback_query(call.id, f"✅ Вы выбрали: {selected_pattern}")

        json_path = os.path.join('temp', 'result.json')
        if not os.path.exists(json_path):
            bot.send_message(user_id, "❌ Ошибка: файл не найден")
            return
        
        try:
            photo_path, first_msg = get_photo.main(
                user_id=user_id,
                pattern=os.path.splitext(selected_pattern)[0],
                file=json_path
            )

            # Отправка сгенерированного документа
            with open(photo_path, 'rb') as photo:
                bot.send_document(user_id, photo, caption=f"🎉 Облако слов сгенерировано успешно!\n\n✨ Ваше первое сообщение:\n'{first_msg}'")

        except Exception as e:
            print(e)
            bot.send_message(user_id, f"❌ Ошибка при генерации: {e}")

        finally:
            try:
                bot.delete_message(user_id, status_msg.message_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение о генерации: {e}")

            if os.path.exists(photo_path):
                os.remove(photo_path)
            # if os.path.exists(json_path):
            #     os.remove(json_path