import os
from instagrapi import Client
from pathlib import Path
from media_loader import MediaLoader
from dotenv import load_dotenv
from telegram import TelegramNotifier
import logging
import schedule
import time

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session_path1 = Path("session1.json")
session_path2 = Path("session2.json")

def login_user(cl, username, password, session_path):
    """ Авторизация пользователя и загрузка сессии. """
    if session_path.exists():
        cl.load_settings(session_path)
    if not cl.login(username, password):
        raise Exception(f"Could not log in as {username}")
    cl.dump_settings(session_path)

def perform_upload(username, password, session_path):
    """ Загрузка контента в Instagram. """
    logger.info(f"Starting upload task for {username}.")
    notifier = TelegramNotifier()
    notifier.notify(f"Toji Everyday: Upload started for {username}")

    try:
        media_loader = MediaLoader("media")
        media_loader.load_media()
        client = Client()
        client.delay_range = [1, 3]
        login_user(client, username, password, session_path)
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
    username1 = os.getenv("INSTA_USERNAME1")
    password1 = os.getenv("INSTA_PASSWORD1")
    username2 = os.getenv("INSTA_USERNAME2")
    password2 = os.getenv("INSTA_PASSWORD2")

    # Настройка расписания для обоих аккаунтов
    schedule.every().day.at("11:00").do(perform_upload, username1, password1, session_path1)
    schedule.every().day.at("11:00").do(perform_upload, username2, password2, session_path2)
    schedule.every().day.at("15:20").do(perform_upload, username1, password1, session_path1)
    schedule.every().day.at("15:25").do(perform_upload, username2, password2, session_path2)

    logger.info("Scheduler started. Waiting for scheduled tasks.")
    while True:
        schedule.run_pending()
        time.sleep(1)
