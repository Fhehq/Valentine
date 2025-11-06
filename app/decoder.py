import zipfile
import os
import logging

logger = logging.getLogger(__name__)

def extract_zip(zip_path):
    extract_to = "temp"
    os.makedirs(extract_to, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            
            if len(files) != 1:
                logger.error(f"В архиве должен быть только один файл — result.json. Найдено файлов: {len(files)}")
                return None

            filename = files[0]
            zip_ref.extractall(extract_to)
            logger.debug(f"Архив успешно распакован: {filename}")
            return os.path.join(extract_to, filename)

    except zipfile.BadZipFile:
        logger.error(f"Файл не является ZIP-архивом или поврежден: {zip_path}")
    except FileNotFoundError:
        logger.error(f"Файл не найден: {zip_path}")
    except IndexError:
        logger.error("Архив пустой")
    except Exception as e:
        logger.error(f"Произошла ошибка при распаковке архива {zip_path}: {e}", exc_info=True)
    
    return None