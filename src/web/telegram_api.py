import asyncio
from aiogram import Bot

from src.bot.api import get_keyboard
from src.bot import keyboards
from src.bot.text import Texts
from src.sql import sql
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


async def send_feedback(chat_id, task_id):
    res = await telegram_api.send_message(chat_id, Texts.new_feedback, Texts.new_feedback.parse_mode,
                                          reply_markup=get_keyboard(keyboards.get_feedback_btn(task_id), row_size=5))
    if res:
        await sql.upd_inline(chat_id, res.message_id, Texts.new_feedback, Texts.new_feedback.parse_mode)
    return res


telegram_api = TelegramAPI()
