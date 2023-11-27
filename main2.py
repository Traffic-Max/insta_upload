import os
from instagrapi import Client
from pathlib import Path
from media_loader import MediaLoader
from dotenv import load_dotenv
from telegram import TelegramNotifier
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def perform_upload(username, password, session_path):
    """ Функция для выполнения загрузки для заданного аккаунта. """
    logger.info(f"Starting upload task for {username}.")
    notifier = TelegramNotifier()
    notifier.notify(f"Toji Everyday: Upload started for {username}")

    try:
        media_loader = MediaLoader("media")
        media_loader.load_media()
        client = Client()
        client.delay_range = [1, 3]

        # Попытка входа
        if session_path.exists():
            client.load_settings(session_path)
        if not client.login(username, password):
            raise Exception(f"Could not log in as {username}")
        client.dump_settings(session_path)

        # Выполнение загрузки
        daily_media = media_loader.get_daily_media()
        daily_media.upload(client)
        daily_story = media_loader.get_daily_story()
        if daily_story is not None:
            daily_story.upload(client, to_story=True)
    except Exception as e:
        logger.error(f"An error occurred during upload for {username}: ", exc_info=True)
        notifier.notify(f"Error for {username}: {e}")
    else:
        notifier.notify(f"Upload finished for {username}")
        logger.info(f"Upload task completed successfully for {username}.")

if __name__ == "__main__":
    load_dotenv()
    username1 = os.getenv("INSTA_USERNAME1", "")
    password1 = os.getenv("INSTA_PASSWORD1", "")
    session_path1 = Path("session1.json")

    username2 = os.getenv("INSTA_USERNAME2", "")
    password2 = os.getenv("INSTA_PASSWORD2", "")
    session_path2 = Path("session2.json")

    # Выполнение загрузки для каждого аккаунта
    perform_upload(username1, password1, session_path1)
    perform_upload(username2, password2, session_path2)
