import asyncio
from aiogram import Bot

from src.utils import config


class TelegramAPI(Bot):
    def __init__(self, **kwargs):
        if 'token' not in kwargs:
            kwargs.update({'token': config['tesseract']['token-iro-mega-bot']})
        super().__init__(**kwargs)

    def __del__(self):
        try:
            asyncio.run(self.close())
        except RuntimeError:
            pass

    async def close(self):
        await self.session.close()

    async def get_username(self):
        me = await self.get_me()
        return me['username']


async def edit_message(chat_id, message_id, text, parse_mode=None, reply_markup=None):
    try:
        await telegram_api.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=reply_markup)
    except:
        await telegram_api.send_message(chat_id, text, parse_mode, reply_markup=reply_markup)


async def delete_message(chat_id, message_id):
    try:
        await telegram_api.delete_message(chat_id, message_id)
    except:
        pass


telegram_api = TelegramAPI()
