import json
import re
from collections import Counter

def get_data(file_name):
    try:
        with open(f"temp/{file_name}", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("Файл не найден")
        return None


def get_all_msg():
    file_name = "result.json"
    data = get_data(file_name)
    
    # Проверяем, что данные загружены успешно
    if data is None:
        print("Данные не найдены, возвращаем пустые значения")
        return None, []
    
    # Проверяем структуру данных
    if "messages" not in data or not data["messages"]:
        print("Структура данных некорректна или сообщения отсутствуют")
        return None, []
    
    all_words = []
    first_msg = data["messages"][0]["text"] if data["messages"][0].get("text") else ""
    
    for msg in data["messages"]:
        if isinstance(msg.get("text"), str):
            text = msg["text"].strip()
            if text and not any(tech_word in text.lower() for tech_word in 
                              ['document_id', 'sticker', 'video_file', 'custom_emoji']):
                
                clean_text = re.sub(r'[^а-яё\s]', ' ', text.lower())
                words = clean_text.split()
                filtered_words = [word for word in words if len(word) >= 3]
                all_words.extend(filtered_words)

    counter = Counter(all_words)
    most_common_150 = counter.most_common(200)
    return first_msg, most_common_150