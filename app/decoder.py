import zipfile
import os

def extract_zip(zip_path):
    extract_to = "temp"
    os.makedirs(extract_to, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            
            if len(files) != 1:
                print("❌ Ошибка: в архиве должен быть только один файл — result.json")
                return None

            filename = files[0]
            zip_ref.extractall(extract_to)
            return os.path.join(extract_to, filename)

    except zipfile.BadZipFile:
        print("❌ Ошибка: файл не является ZIP-архивом или поврежден")
    except FileNotFoundError:
        print(f"❌ Ошибка: файл {zip_path} не найден")
    except IndexError:
        print("❌ Ошибка: архив пустой")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
    
    return None