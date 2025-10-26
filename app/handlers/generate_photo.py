from telebot import types
import os
import sys
sys.path.append(os.getcwd())
import get_photo
from app.decoder import extract_zip

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
            msg_text += f"{idx}: {os.path.splitext(pattern)[0]}\n"

        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            types.InlineKeyboardButton(str(i), callback_data=f"pattern_{i-1}")
            for i in range(1, len(pattern_files) + 1)
        ]
        markup.add(*buttons)

        bot.send_message(message.chat.id, msg_text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('pattern_'))
    def handle_pattern_choice(call):
        index = int(call.data.split('_')[1])
        patterns_dir = 'patterns'
        pattern_files = [f for f in os.listdir(patterns_dir)]
        user_id = call.from_user.id

        if index >= len(pattern_files):
            bot.answer_callback_query(call.id, "❌ Ошибка выбора")
            return

        selected_pattern = pattern_files[index]
        bot.answer_callback_query(call.id, f"✅ Вы выбрали: {selected_pattern}")

        msg = bot.send_message(
            user_id,
            f"📁 Теперь отправь ZIP-архив с перепиской (только один файл формата json)\nСсылка как получить историю чата и сделать ZIP архив - [тут](https://t.me/valentine_guide)\n\n"
            f"Паттерн: *{os.path.splitext(selected_pattern)[0]}*",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, handle_zip_upload, selected_pattern)

    def handle_zip_upload(message, selected_pattern):
        user_id = message.from_user.id

        if not message.document:
            error_msg = bot.send_message(user_id, "❌ Отправь именно ZIP-архив, а не текст. Попробуй еще раз:")
            bot.register_next_step_handler(error_msg, handle_zip_upload, selected_pattern)
            return 

        if not message.document.file_name.lower().endswith('.zip'):
            error_msg = bot.send_message(user_id, "⚠️ Нужен файл в формате .zip. Попробуй еще раз:")
            bot.register_next_step_handler(error_msg, handle_zip_upload, selected_pattern)
            return

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        temp_dir = 'temp'
        os.makedirs(temp_dir, exist_ok=True)
        zip_path = os.path.join(temp_dir, f"{user_id}.zip")

        with open(zip_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        json_path = extract_zip(zip_path)
        if not json_path or not os.path.exists(json_path):
            bot.send_message(user_id, "❌ В архиве должен быть только один файл — result.json.")
            return
        
        status_msg = bot.send_message(user_id, "🧬 Генерация фото...")
        
        if os.path.exists(zip_path):
            os.remove(zip_path)

        try:
            photo_path, first_msg = get_photo.main(
                user_id=user_id,
                pattern=os.path.splitext(selected_pattern)[0],
                file=json_path
            )

            with open(photo_path, 'rb') as photo:
                bot.send_document(
                    user_id,
                    photo,
                    caption=f"🎉 Облако слов сгенерировано успешно!\n\n✨ Первое сообщение:\n'{first_msg}'"
                )

        except Exception as e:
            print(e)
            bot.send_message(user_id, f"❌ Ошибка при генерации: {e}")

        finally:
            try:
                bot.delete_message(user_id, status_msg.message_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение о генерации: {e}")

            if os.path.exists(json_path):
                os.remove(json_path)
            if os.path.exists(photo_path):
                os.remove(photo_path)
