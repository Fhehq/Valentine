
import os
import random
from typing import List, Tuple, Dict, Optional
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
        
        os.makedirs(config.get('patterns_dir', 'patterns'), exist_ok=True)
        os.makedirs(config.get('output_dir', 'outputs'), exist_ok=True)
        
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
        
        while len(expanded) < target_count:
            expanded.extend(words)
    
        while len(expanded) < target_count:
            word = random.choice(words)
            expanded.append(word)
        
        return expanded[:target_count]
    
    def _create_custom_color_func(self, color_scheme: List[str]):
        """Создает функцию цвета на основе цветовой схемы"""
        def color_func(word=None, font_size=None, position=None, orientation=None, random_state=None, **kwargs):
            return random.choice(color_scheme)
        return color_func

    def generate_custom_shape_wordcloud(self, words: List[str], pattern_path: str, 
                                    output_path: str) -> bool:
        """Генератор облака слов с оптимизацией размера файла"""
        if not WORDCLOUD_AVAILABLE:
            print("Ошибка: Библиотека wordcloud недоступна")
            return False
        

        expanded_words = self._expand_word_list(words, target_count=200)
        
        try:
            img = Image.open(pattern_path)
            
            if img.mode == 'RGBA':
                arr = np.array(img)
                alpha = arr[:,:,3]
                mask = np.where(alpha == 255, 0, 255).astype(np.uint8)
                        
            else:
                gray = np.array(img.convert('L'))
                mask = np.where(gray == 255, 0, 255).astype(np.uint8)
            
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
            'relative_scaling': 0.5,
            'colormap': None,
            'color_func': color_func,
            'prefer_horizontal': 0.8,
            'margin': 0,
            'background_color': None,
            'mode': 'RGBA',
            'font_path': self.font_path,
            'random_state': 42,
            'collocations': False,
            'normalize_plurals': False,
            'include_numbers': False,
            'min_word_length': 2,
            'repeat': True,
            'contour_width': 0,
            'contour_color': None,
        }
        
        try:
            wordcloud = BaseWordCloud(**wordcloud_config)
            wordcloud.generate_from_frequencies(word_freq)
            image = wordcloud.to_image()

            return self._optimize_and_save_image(image, output_path)
            
        except Exception as e:
            print(f"Ошибка при создании облака слов: {e}")
            return False

    def _optimize_and_save_image(self, image: Image.Image, output_path: str) -> bool:
        """Оптимизирует и сохраняет изображение с минимальным размером файла"""
        try:
            image.save(
                output_path, 
                'PNG', 
                optimize=True,
                compress_level=6,
            )
            file_size = os.path.getsize(output_path)
            print(f"Размер файла после сохранения: {file_size} байт ({file_size/1024:.1f} KB)")
            
            if file_size > 2 * 1024 * 1024:
                print("Файл слишком большой, применяем дополнительную оптимизацию...")
                return self._further_optimize_image(image, output_path)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении изображения: {e}")
            return False

    def _further_optimize_image(self, image: Image.Image, output_path: str) -> bool:
        try:
            if image.mode == 'RGBA':
                image = image.convert('RGBA')
                
                temp_image = image.convert('RGB')
                temp_image = temp_image.convert('P', palette=Image.ADAPTIVE, colors=128)
                alpha = image.split()[-1]
                mask = Image.eval(alpha, lambda a: 255 if a > 0 else 0)
                temp_image.putalpha(mask)
                
                image = temp_image
            
            image.save(
                output_path,
                'PNG',
                optimize=True,
                compress_level=9,
            )
            
            final_size = os.path.getsize(output_path)
            print(f"Размер после дополнительной оптимизации: {final_size} байт ({final_size/1024:.1f} KB)")
            
            return True
        
        except Exception as e:
            print(f"Ошибка дополнительной оптимизации: {e}")
            try:
                image.save(output_path, 'PNG', optimize=True, compress_level=9)
                return True
            except:
                return False

def get_words_from_messages(file_name) -> List[str]:
    """Получает слова из сообщений используя существующий модуль"""
    try:
        from get_msg import get_all_msg
        first_msg, most_common_words = get_all_msg(file_name)
        words = [word for word, count in most_common_words]
        print(f"Загружено {len(words)} слов из сообщений (все доступные слова)")
        return words, first_msg
        
    except Exception as e:
        print(f"Ошибка загрузки слов из сообщений: {e}")
        return None

def main(user_id=0, pattern=None, file=None):
    """Основная функция программы — генерация облака слов"""
    if not pattern:
        print("❌ Ошибка: не указан паттерн")
        return None, None

    pattern = f"{pattern}.png"
    
    config = {
        'width': 600,
        'height': 600,
        'min_font_size': 6,
        'max_font_size': 100,
        'min_spacing': 1,
        'max_rotation': 45,
        'patterns_dir': 'patterns',
        'output_dir': 'outputs',
        'font_path': None,
    }

    os.makedirs(config['output_dir'], exist_ok=True)

    words, first_msg = get_words_from_messages(file_name=file)
    if words is None:
        print("Ошибка загрузки слов")
        return None, None

    generator = DenseWordCloudGenerator(config)
    pattern_path = os.path.join(config['patterns_dir'], pattern)
    
    if not os.path.exists(pattern_path):
        print(f"❌ Ошибка: файл паттерна не найден {pattern_path}")
        return None, first_msg

    output_filename = f"{os.path.splitext(pattern)[0]}_user_id-{user_id}.png"
    output_path = os.path.join(config['output_dir'], output_filename)

    success = generator.generate_custom_shape_wordcloud(words, pattern_path, output_path)
    if not success:
        print(f"❌ Ошибка при создании облака слов в форме '{pattern}'")
        return None, first_msg

    print(f"✅ Облако слов создано: {output_path}")
    return output_path, first_msg