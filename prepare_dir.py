import os
import yaml
from pathlib import Path

class Config:
    def __init__(self, caption):
        self.is_story = False
        self.is_feed = True
        self.is_easter_egg = False
        self.caption = caption

    def save_to_yaml(self, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(self.__dict__, f, allow_unicode=True)

def prepare_directory_for_upload(source_directory, destination_directory):
    all_files = os.listdir(source_directory)
    posts = {}

    # Группировка файлов по таймштампам
    for file in all_files:
        if file.endswith('.mp4') or file.endswith('.txt') or file.endswith('.jpg'):
            timestamp = file.split('_')[0]
            posts.setdefault(timestamp, []).append(file)

    # Обработка каждого поста
    for timestamp, files in posts.items():
        post_dir = Path(destination_directory) / timestamp
        post_dir.mkdir(exist_ok=True)
        caption_text = ""

        for file in files:
            file_path = Path(source_directory) / file
            if file.endswith('.mp4'):
                new_file_path = post_dir / "media.mp4"
            elif file.endswith('.txt'):
                new_file_path = post_dir / "caption.txt"
                with open(file_path, 'r', encoding='utf-8') as f:  # Указываем кодировку UTF-8 здесь
                    caption_text = f.read()
            elif file.endswith('.jpg'):
                new_file_path = post_dir / "thumbnail.jpg"

            # Проверка существования файла и удаление, если необходимо
            if new_file_path.exists():
                os.remove(new_file_path)

            os.rename(file_path, new_file_path)

        # Создание файла конфигурации
        config = Config(caption=caption_text)
        config.save_to_yaml(post_dir / "config.yaml")

# Пример использования
source_dir = r"C:\Users\PC\Projects\toji_everyday\nastya.jolly"
destination_dir = r"C:\Users\PC\Projects\toji_everyday\media"
prepare_directory_for_upload(source_dir, destination_dir)
