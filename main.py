#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор плотных облаков слов в пользовательских формах
Версия 3.0 - Использует официальную библиотеку wordcloud из pip
"""

import os
import random
import math
import time
from typing import List, Tuple, Dict, Optional
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json

# Импортируем установленную библиотеку wordcloud
try:
    from wordcloud import WordCloud as BaseWordCloud, STOPWORDS, random_color_func
    WORDCLOUD_AVAILABLE = True
    print("✓ Библиотека wordcloud успешно загружена")
except ImportError as e:
    WORDCLOUD_AVAILABLE = False
    print(f"Ошибка: wordcloud не установлен. Установите через: pip install wordcloud")


class DenseWordCloudGenerator:
    """Генератор плотных облаков слов с поддержкой пользовательских форм"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.width = config.get('width', 1200)
        self.height = config.get('height', 1200)
        self.min_font_size = config.get('min_font_size', 6)
        self.max_font_size = config.get('max_font_size', 100)
        self.min_spacing = config.get('min_spacing', 1)
        self.max_rotation = config.get('max_rotation', 45)
        self.color_schemes = config.get('color_schemes', self._get_default_color_schemes())
        self.font_path = config.get('font_path', None)
        
        # Создаем папки если не существуют
        os.makedirs(config.get('patterns_dir', 'patterns'), exist_ok=True)
        os.makedirs(config.get('output_dir', 'outputs'), exist_ok=True)
        
        # Инициализируем шрифты
        self._init_fonts()
        
    def _get_default_color_schemes(self) -> List[List[str]]:
        """Возвращает наборы цветовых схем по умолчанию"""
        return [
            ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],  # Яркие пастельные
            ['#2C3E50', '#E74C3C', '#F39C12', '#27AE60', '#8E44AD'],  # Контрастные
            ['#FF9A9E', '#FECFEF', '#FECFEF', '#FF9A9E', '#FECFEF'],  # Розовые оттенки
            ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'],   # Градиентные
            ['#ffecd2', '#fcb69f', '#ff8a80', '#ff80ab', '#ea80fc'],  # Теплые тона
            ['#a8edea', '#fed6e3', '#d299c2', '#fef9d7', '#667eea'],  # Нежные пастели
        ]
    
    def _init_fonts(self):
        """Инициализирует шрифты для разных размеров"""
        self.fonts = {}
        try:
            font_to_use = self.font_path
            
            for size in range(self.min_font_size, self.max_font_size + 1, 2):
                if font_to_use and os.path.exists(font_to_use):
                    try:
                        self.fonts[size] = ImageFont.truetype(font_to_use, size)
                    except:
                        self.fonts[size] = ImageFont.load_default()
                else:
                    # Пробуем системные шрифты
                    try:
                        self.fonts[size] = ImageFont.truetype("arial.ttf", size)
                    except:
                        try:
                            self.fonts[size] = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
                        except:
                            self.fonts[size] = ImageFont.load_default()
        except Exception as e:
            print(f"Предупреждение: Не удалось загрузить шрифты: {e}")
            # Используем шрифт по умолчанию
            for size in range(self.min_font_size, self.max_font_size + 1, 2):
                self.fonts[size] = ImageFont.load_default()
    
    def _expand_word_list(self, words: List[str], target_count: int) -> List[str]:
        """Расширяет список слов до целевого количества"""
        if len(words) >= target_count:
            return words
        
        expanded = words.copy()
        
        # Если слов недостаточно, повторяем существующие
        while len(expanded) < target_count:
            expanded.extend(words)
        
        # Если все еще недостаточно, дублируем существующие слова
        while len(expanded) < target_count:
            word = random.choice(words)
            expanded.append(word)
        
        return expanded[:target_count]
    
    def _create_custom_color_func(self, color_scheme: List[str]):
        """Создает функцию цвета на основе цветовой схемы"""
        def color_func(word=None, font_size=None, position=None, orientation=None, random_state=None, **kwargs):
            return random.choice(color_scheme)
        return color_func
    
    def generate_rectangle_wordcloud(self, words: List[str], output_path: str) -> bool:
        """Генерирует прямоугольное облако слов с максимальной плотностью используя wordcloud"""
        print(f"Генерация прямоугольного облака слов...")
        
        if not WORDCLOUD_AVAILABLE:
            print("Ошибка: Библиотека wordcloud недоступна")
            return False
        
        # Расширяем список слов для достижения 150+ уникальных слов
        expanded_words = self._expand_word_list(words, target_count=150)
        print(f"Расширенный список: {len(expanded_words)} слов")
        
        # Выбираем цветовую схему
        color_scheme = random.choice(self.color_schemes)
        color_func = self._create_custom_color_func(color_scheme)
        
        # Создаем словарь частот
        word_freq = Counter(expanded_words)
        
        # Настройки для максимальной плотности
        wordcloud_config = {
            'width': self.width,
            'height': self.height,
            'max_words': len(expanded_words),
            'min_font_size': self.min_font_size,
            'max_font_size': self.max_font_size,
            'relative_scaling': 0.5,  # Более равномерное распределение размеров
            'colormap': None,
            'color_func': color_func,
            'prefer_horizontal': 0.7,  # Больше горизонтальных слов
            'margin': self.min_spacing,  # Минимальные отступы
            'background_color': None,  # Прозрачный фон
            'mode': 'RGBA',
            'font_path': self.font_path,
            'random_state': 42,
            'collocations': False,  # Отключаем коллокации для лучшего контроля
            'normalize_plurals': False,
            'include_numbers': False,
            'min_word_length': 2,
            'repeat': True,  # Разрешаем повторения для заполнения
        }
        
        try:
            # Создаем WordCloud объект
            wordcloud = BaseWordCloud(**wordcloud_config)
            
            # Генерируем облако слов
            wordcloud.generate_from_frequencies(word_freq)
            
            # Получаем изображение
            image = wordcloud.to_image()
            
            # Сохраняем с максимальным качеством
            image.save(output_path, 'PNG', optimize=False, compress_level=0)
            
            print(f"Прямоугольное облако слов создано: {output_path}")
            print(f"Размещено слов: {len(word_freq)}")
            print(f"Уникальных слов: {len(set(expanded_words))}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка при создании облака слов: {e}")
            return False
    
    def generate_custom_shape_wordcloud(self, words: List[str], pattern_path: str, 
                                      output_path: str) -> bool:
        """Генерирует облако слов в пользовательской форме используя wordcloud"""
        print(f"Генерация облака слов для формы: {os.path.basename(pattern_path)}")
        
        if not WORDCLOUD_AVAILABLE:
            print("Ошибка: Библиотека wordcloud недоступна")
            return False
        
        # Расширяем список слов для максимальной плотности
        expanded_words = self._expand_word_list(words, target_count=200)
        
        # Загружаем маску
        try:
            img = Image.open(pattern_path)
            
            # Если изображение имеет альфа-канал, используем его
            if img.mode == 'RGBA':
                arr = np.array(img)
                # Используем альфа-канал как маску
                alpha = arr[:,:,3]  # Альфа-канал
                
                # Создаем бинарную маску: ИНВЕРТИРУЕМ для wordcloud!
                # В wordcloud: 0 = можно размещать слова, 255 = нельзя размещать слова
                # У нас: 255 = форма (можно), 0 = фон (нельзя)
                # Поэтому инвертируем: форма (255) -> 0, фон (0) -> 255
                mask = np.where(alpha == 255, 0, 255).astype(np.uint8)
                
                print(f"Бинарная маска создана:")
                print(f"  - Области для размещения слов (255): {np.sum(mask == 255)} пикселей")
                print(f"  - Запрещенные области (0): {np.sum(mask == 0)} пикселей")
                
            else:
                # Для изображений без альфа-канала конвертируем в оттенки серого
                gray = np.array(img.convert('L'))
                # Создаем бинарную маску: ИНВЕРТИРУЕМ для wordcloud!
                # Белые области (255) = форма -> 0 (можно размещать)
                # Черные области (0) = фон -> 255 (нельзя размещать)
                mask = np.where(gray == 255, 0, 255).astype(np.uint8)
                
                print(f"Бинарная маска создана из оттенков серого:")
                print(f"  - Области для размещения слов (255): {np.sum(mask == 255)} пикселей")
                print(f"  - Запрещенные области (0): {np.sum(mask == 0)} пикселей")
            
            print(f"Маска загружена: размер {mask.shape}, тип {mask.dtype}")
            print(f"Уникальные значения маски: {np.unique(mask)}")
            
        except Exception as e:
            print(f"Ошибка загрузки маски из {pattern_path}: {e}")
            return False
        
        # Выбираем цветовую схему
        color_scheme = random.choice(self.color_schemes)
        color_func = self._create_custom_color_func(color_scheme)
        
        # Создаем словарь частот
        word_freq = Counter(expanded_words)
        wordcloud_config = {
            'width': self.width,
            'height': self.height,
            'mask': mask,
            'max_words': len(expanded_words),
            'min_font_size': self.min_font_size,
            'max_font_size': self.max_font_size,
            'relative_scaling': 0.5,  # Более равномерное распределение размеров
            'colormap': None,
            'color_func': color_func,
            'prefer_horizontal': 0.8,  # Больше горизонтальных слов для плотности
            'margin': 0,  # Минимальные отступы для максимальной плотности
            'background_color': None,
            'mode': 'RGBA',
            'font_path': self.font_path,
            'random_state': 42,
            'collocations': False,
            'normalize_plurals': False,
            'include_numbers': False,
            'min_word_length': 2,
            'repeat': True,
            'contour_width': 0,  # Убираем контуры
            'contour_color': None,
        }
        
        try:
            # Создаем WordCloud объект
            wordcloud = BaseWordCloud(**wordcloud_config)
            
            # Генерируем облако слов
            wordcloud.generate_from_frequencies(word_freq)
            
            # Получаем изображение
            image = wordcloud.to_image()
            
            # Сохраняем с максимальным качеством
            image.save(output_path, 'PNG', optimize=False, compress_level=0)
            
            print(f"Облако слов в форме создано: {output_path}")
            print(f"Размещено слов: {len(word_freq)}")
            print(f"Уникальных слов: {len(set(expanded_words))}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка при создании облака слов: {e}")
            return False
    
    def batch_generate(self, words: List[str], patterns_dir: str, output_dir: str) -> Dict[str, bool]:
        """Пакетная генерация облаков слов для всех паттернов"""
        results = {}
        
        if not os.path.exists(patterns_dir):
            print(f"Папка с паттернами не найдена: {patterns_dir}")
            return results
        
        pattern_files = [f for f in os.listdir(patterns_dir) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # Фильтруем тестовые и демо файлы
        pattern_files = [f for f in pattern_files 
                        if not any(keyword in f.lower() for keyword in ['test', 'demo', 'temp', 'tmp'])]
        
        if not pattern_files:
            print(f"В папке {patterns_dir} не найдено изображений (исключены тестовые файлы)")
            return results
        
        print(f"Найдено {len(pattern_files)} паттернов для обработки")
        
        for i, pattern_file in enumerate(pattern_files, 1):
            pattern_path = os.path.join(patterns_dir, pattern_file)
            output_filename = f"{os.path.splitext(pattern_file)[0]}_wordcloud.png"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"\n[{i}/{len(pattern_files)}] Обработка: {pattern_file}")
            
            try:
                success = self.generate_custom_shape_wordcloud(words, pattern_path, output_path)
                results[pattern_file] = success
                
                if success:
                    print(f"✓ Успешно создано: {output_filename}")
                else:
                    print(f"✗ Ошибка при создании: {output_filename}")
                    
            except Exception as e:
                print(f"✗ Ошибка при обработке {pattern_file}: {e}")
                results[pattern_file] = False
        
        return results


def get_words_from_messages() -> List[str]:
    """Получает слова из сообщений используя существующий модуль"""
    try:
        from get_msg import get_all_msg
        first_msg, most_common_words = get_all_msg()
        
        words = [word for word, count in most_common_words]
        print(f"Загружено {len(words)} слов из сообщений (все доступные слова)")
        return words
        
    except Exception as e:
        print(f"Ошибка загрузки слов из сообщений: {e}")
        return get_default_words()


def get_default_words() -> List[str]:
    """Возвращает список слов по умолчанию для тестирования"""
    return [
        "любовь", "мечта", "мир", "счастье", "память", "свобода", "надежда", "радость",
        "красота", "дружба", "семья", "дом", "путешествие", "приключение", "музыка",
        "книга", "искусство", "природа", "солнце", "звезда", "луна", "море", "горы",
        "лес", "цветок", "птица", "бабочка", "снег", "дождь", "радуга", "ветер",
        "огонь", "вода", "земля", "воздух", "время", "жизнь", "смерть", "рождение",
        "детство", "юность", "зрелость", "старость", "молодость", "мудрость", "знание",
        "учение", "работа", "отдых", "сон", "бодрствование", "утро", "день", "вечер",
        "ночь", "зима", "весна", "лето", "осень", "январь", "февраль", "март",
        "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь",
        "декабрь", "понедельник", "вторник", "среда", "четверг", "пятница", "суббота",
        "воскресенье", "завтрак", "обед", "ужин", "чай", "кофе", "хлеб", "молоко",
        "сахар", "соль", "перец", "масло", "сыр", "мясо", "рыба", "овощи", "фрукты"
    ]


def main():
    """Основная функция программы"""
    print("=" * 60)
    print("ГЕНЕРАТОР ПЛОТНЫХ ОБЛАКОВ СЛОВ В ПОЛЬЗОВАТЕЛЬСКИХ ФОРМАХ")
    print("Версия 3.0 - Интегрированная с библиотекой wordcloud")
    print("=" * 60)
    
    # Конфигурация
    config = {
        'width': 1200,
        'height': 1200,
        'min_font_size': 6,      
        'max_font_size': 100,    
        'min_spacing': 1,        
        'max_rotation': 45,      
        'patterns_dir': 'patterns',
        'output_dir': 'outputs',
        'font_path': None,
    }
    
    # Получаем слова
    print("\n1. Загрузка слов...")
    words = get_words_from_messages()
    
    if not words:
        print("Используем слова по умолчанию")
        words = get_default_words()
    
    print(f"Загружено {len(words)} слов")
    
    print("\n2. Инициализация генератора...")
    generator = DenseWordCloudGenerator(config)
    
    # Показываем доступные паттерны
    patterns_dir = config['patterns_dir']
    if not os.path.exists(patterns_dir):
        print(f"❌ Папка с паттернами не найдена: {patterns_dir}")
        return
    
    pattern_files = [f for f in os.listdir(patterns_dir) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Фильтруем тестовые и демо файлы
    pattern_files = [f for f in pattern_files 
                    if not any(keyword in f.lower() for keyword in ['test', 'demo', 'temp', 'tmp'])]
    
    if not pattern_files:
        print(f"❌ В папке {patterns_dir} не найдено изображений (исключены тестовые файлы)")
        return
    
    print(f"\n📁 Найдено {len(pattern_files)} паттернов:")
    for i, pattern in enumerate(pattern_files, 1):
        print(f"  {i}. {os.path.splitext(pattern)[0]}")
    
    # Выбор типа генерации
    print(f"\n🎨 Выберите тип генерации:")
    print("1. Облако слов в выбранной форме")
    print("2. Все формы сразу")
    
    while True:
        try:
            choice = input("\nВведите номер (1-3): ").strip()
            if choice in ['1', '2']:
                break
            else:
                print("❌ Пожалуйста, введите 1, 2")
        except KeyboardInterrupt:
            print("\n👋 Программа прервана пользователем")
            return
    

    if choice == '1':
        # Облако слов в выбранной форме
        print(f"\n🎨 Выберите форму для облака слов:")
        for i, pattern in enumerate(pattern_files, 1):
            print(f"  {i}. {os.path.splitext(pattern)[0]}")
        
        while True:
            try:
                pattern_choice = input(f"\nВведите номер формы (1-{len(pattern_files)}): ").strip()
                pattern_index = int(pattern_choice) - 1
                if 0 <= pattern_index < len(pattern_files):
                    selected_pattern = pattern_files[pattern_index]
                    break
                else:
                    print(f"❌ Пожалуйста, введите число от 1 до {len(pattern_files)}")
            except ValueError:
                print("❌ Пожалуйста, введите корректный номер")
            except KeyboardInterrupt:
                print("\n👋 Программа прервана пользователем")
                return
        
        print(f"\n" + "=" * 40)
        print(f"ГЕНЕРАЦИЯ ОБЛАКА СЛОВ В ФОРМЕ: {os.path.splitext(selected_pattern)[0].upper()}")
        print("=" * 40)
        
        pattern_path = os.path.join(patterns_dir, selected_pattern)
        output_filename = f"{os.path.splitext(selected_pattern)[0]}_wordcloud.png"
        output_path = os.path.join(config['output_dir'], output_filename)
        
        success = generator.generate_custom_shape_wordcloud(words, pattern_path, output_path)
        
        if success:
            print(f"✅ Облако слов в форме '{os.path.splitext(selected_pattern)[0]}' создано успешно!")
        else:
            print(f"❌ Ошибка при создании облака слов в форме '{os.path.splitext(selected_pattern)[0]}'")
    
    elif choice == '2':
        # Все формы сразу
        print("\n" + "=" * 40)
        print("ГЕНЕРАЦИЯ ВСЕХ ФОРМ")
        print("=" * 40)
        
        # Сначала прямоугольное
        print("\n📦 Создание прямоугольного облака слов...")
        rectangle_output = os.path.join(config['output_dir'], 'rectangle_wordcloud.png')
        rectangle_success = generator.generate_rectangle_wordcloud(words, rectangle_output)
        
        if rectangle_success:
            print("✅ Прямоугольное облако слов создано!")
        else:
            print("⚠️ Прямоугольное облако слов не создано")
        
        # Затем все формы
        print(f"\n🎨 Создание облаков слов для всех форм...")
        results = generator.batch_generate(words, patterns_dir, config['output_dir'])
        
        # Статистика
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\n📊 Статистика:")
        print(f"  • Всего форм: {total}")
        print(f"  • Успешно создано: {successful}")
        print(f"  • Ошибок: {total - successful}")
        
        if successful > 0:
            print(f"\n✅ Успешно созданные файлы:")
            for pattern, success in results.items():
                if success:
                    output_name = f"{os.path.splitext(pattern)[0]}_wordcloud.png"
                    print(f"  • {output_name}")
    
    print(f"\n📁 Все файлы сохранены в папке: {config['output_dir']}")
    print("=" * 60)


if __name__ == "__main__":
    main()