import os
import logging
from instagrapi import Client
from pathlib import Path
from media_loader import MediaLoader
from dotenv import load_dotenv
import telebot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
bot = telebot.TeleBot(bot_token)

class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance

class TelegramNotifier(metaclass=Singleton):
    def __init__(self):
        self.bot = telebot.TeleBot(bot_token)
        self.chat_id = chat_id

    def notify(self, message) -> None:
        try:
            self.bot.send_message(self.chat_id, message)
            logger.info(message)
        except Exception as e:
            logger.info(f"Could not send Telegram message: {e}")

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

        if session_path.exists():
            client.load_settings(session_path)
        if not client.login(username, password):
            raise Exception(f"Could not log in as {username}")
        client.dump_settings(session_path)

        daily_media = media_loader.get_daily_media()
        daily_media.upload(client)
        daily_story = media_loader.get_daily_story()
        if daily_story is not None:
            daily_story.upload(client, to_story=True)
    except Exception as e:
        notifier.notify(f"Error for {username}: {e}")
        logger.error(f"An error occurred during upload for {username}: ", exc_info=True)
    else:
        notifier.notify(f"Upload finished for {username}")
        logger.info(f"Upload task completed successfully for {username}.")

@bot.message_handler(commands=['upload'])
def handle_upload_command(message):
    """ Обработчик команды /upload для Telegram. """
    try:
        username1 = os.getenv("INSTA_USERNAME1", "")
        password1 = os.getenv("INSTA_PASSWORD1", "")
        session_path1 = Path("session1.json")

        username2 = os.getenv("INSTA_USERNAME2", "")
        password2 = os.getenv("INSTA_PASSWORD2", "")
        session_path2 = Path("session2.json")

        perform_upload(username1, password1, session_path1)
        perform_upload(username2, password2, session_path2)

        bot.reply_to(message, "Upload started for both accounts.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")
        logger.error("Error in Telegram command handler: ", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting Telegram bot.")
    bot.polling(none_stop=True)
