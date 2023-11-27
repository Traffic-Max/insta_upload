from abc import ABC, abstractmethod
import os
import datetime
import random
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import yaml
from instagrapi import Client

logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)
logger.setLevel(logging.INFO)

DEFAULT_CAPTION = """👆 Контакты по ссылке в профиле 💌\n\n#знакомстваукраина #знакомствакиев #знакомстваодесса #девушкиукраины #девушкиукраина #девушкикиев #девушкиодесса #девушкихарькова #девушкихарьков #девушкидонецк #девушкидонецка #девушкиднепр\n#знакомства #знакомстваонлаи‌н\n#дружба #свидание #отношения #ищудевушку #красивыедами #познакомиться #ищужену #ищулюбовь #ищумужа #хочузамуж #znakomstva #ищужену #ищуженщину #женюсь #сайтзнакомств"""

START_DAY = datetime.datetime(2023, 11, 5)

class Config(BaseModel):
    is_story: bool = False
    is_feed: bool = True
    is_easter_egg: bool = False
    caption: str = ""

    @classmethod
    def load(cls, config_file) -> 'Config':
        with open(config_file, 'r', encoding='utf-8') as f:  # Указываем кодировку UTF-8
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
        new_config = cls.parse_obj(config)
        new_config.caption = new_config.set_publication_day(new_config.caption)
        return new_config

    def set_publication_day(self, caption: str) -> str:
        publication_day = datetime.datetime.today() - START_DAY
        caption = f"{caption}\n{DEFAULT_CAPTION}"
        return caption

    def save(self, config_file):
        with open(config_file, "w") as f:
            yaml.dump(self.dict(), f, default_flow_style=False)

class Media(ABC):
    def __init__(self, file_path: Path, config: Config, thumbnail_path: Optional[Path] = None):
        self.file_path = file_path
        self.thumbnail_path = thumbnail_path if thumbnail_path is not None else file_path.parent / "thumbnail.jpg"
        self.config = config
        self.thumbnail_exists = thumbnail_path is not None and thumbnail_path.exists()

    @abstractmethod
    def upload(self, client: Client, to_story: bool = False):
        pass

    def default_thumbnail(self):
        default_thumbnail_path = str(self.file_path) + ".jpg"
        os.rename(default_thumbnail_path, self.thumbnail_path)

class Image(Media):
    def upload(self, client: Client, to_story: bool = False):
        if to_story and self.config.is_story:
            client.photo_upload_to_story(self.file_path, self.config.caption)
        else:
            client.photo_upload(self.file_path, self.config.caption)

class Video(Media):
    def upload(self, client: Client, to_story: bool = False):
        kwargs = {"thumbnail": self.thumbnail_path} if self.thumbnail_exists else {}
        if to_story and self.config.is_story:
            client.video_upload_to_story(self.file_path, self.config.caption, **kwargs)
        else:
            client.video_upload(self.file_path, self.config.caption, **kwargs)

class MediaFactory:
    @staticmethod
    def create_media(file_path: Path, config_path: Path, thumbnail_path: Optional[Path] = None) -> Media:
        config = Config.load(config_path)
        if file_path.suffix == ".jpg":
            return Image(file_path, config, thumbnail_path)
        elif file_path.suffix == ".mp4":
            return Video(file_path, config, thumbnail_path)
        else:
            raise ValueError(f"Invalid media file extension: {file_path.suffix}")

class MediaLoader:
    MEDIA_FILENAME = "media"
    THUMBNAIL_FILENAME = "thumbnail.jpg"
    CONFIG_FILENAME = "config.yaml"

    def __init__(self, directory):
        self.directory = directory
        self.media = []
        self.stories = []
        self.easter_eggs = []

    def load_media(self):
        for directory in os.listdir(self.directory):
            directory_path = Path(self.directory) / directory
            if directory_path.is_dir():
                media_path = None
                thumbnail_path = None
                config_path = directory_path / self.CONFIG_FILENAME

                for file in os.listdir(directory_path):
                    file_path = directory_path / file
                    if self.MEDIA_FILENAME in file:
                        media_path = file_path
                    elif self.THUMBNAIL_FILENAME in file:
                        thumbnail_path = file_path

                if media_path and config_path.exists():
                    media = MediaFactory.create_media(media_path, config_path, thumbnail_path)
                    if media.config.is_story:
                        self.stories.append(media)
                    if media.config.is_easter_egg:
                        self.easter_eggs.append(media)
                    if media.config.is_feed:
                        self.media.append(media)
        if not self.media:
            raise ValueError("No media found in directory")

    def get_daily_media(self) -> Media:
        if self.media:
            return self.media[random.randint(0, len(self.media) - 1)]
        else:
            raise ValueError("No media found")

    def get_daily_story(self) -> Optional[Media]:
        random_number = random.randint(1, 365)
        today = datetime.datetime.today()
        if self.easter_eggs and random_number == today.timetuple().tm_yday:
            return self.easter_eggs[random.randint(0, len(self.easter_eggs) - 1)]
        elif self.stories:
            return self.stories[random.randint(0, len(self.stories) - 1)]
        else:
            return None
