import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
from polybot.img_proc import Img

class Bot:
    """
    The Bot class is a simple echo bot that communicates with Telegram servers.
    """

    def __init__(self, token, telegram_chat_url):
        """
        Initializes the Bot with a token and a Telegram chat URL.

        :param token: The Telaegram bot token.
        :param telegram_chat_url: The URL of the Telegram chat.
        """
        self.telegram_bot_client = telebot.TeleBot(token)
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)
        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        """
        Sends a text message to a chat.

        :param chat_id: The ID of the chat to send the message to.
        :param text: The text of the message to send.
        """
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        """
        Sends a text message to a chat, quoting another message.

        :param chat_id: The ID of the chat to send the message to.
        :param text: The text of the message to send.
        :param quoted_msg_id: The ID of the message to quote.
        """
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        """
        Checks if the current message is a photo.

        :param msg: The message to check.
        :return: True if the message is a photo, False otherwise.
        """
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photo that was sent to the Bot to `photos` directory.

        :param msg: The message containing the photo.
        :return: The path of the downloaded photo.
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        """
        Sends a photo to a chat.

        :param chat_id: The ID of the chat to send the photo to.
        :param img_path: The path of the photo to send.
        """
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """
        Handles incoming messages. This method should be overridden by subclasses.

        :param msg: The incoming message.
        """
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    """
    The QuoteBot class extends the Bot class to quote incoming messages.
    """

    def handle_message(self, msg):
        """
        Handles incoming messages by quoting them.

        :param msg: The incoming message.
        """
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ImageProcessingBot(Bot):
    """
    The ImageProcessingBot class extends the Bot class to process incoming photo messages.
    """

    def handle_message(self, msg):
        """
        Handles incoming photo messages by processing them and sending them back to the user.

        :param msg: The incoming message.
        """
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            img_path = self.download_user_photo(msg)
            img = Img(img_path)
            img.rotate()
            img.salt_n_pepper()
            img_path = 'rotated_' + img_path
            img.save(img_path)
            self.send_photo(msg['chat']['id'], img_path)
        else:
            self.send_text(msg['chat']['id'], 'Please send a photo')
        # save the filtered image to a new file
        filtered_img_path = img.save_img()
        # send the filtered image to the user
        self.send_photo(msg['chat']['id'], filtered_img_path)


