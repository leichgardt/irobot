import asyncio
import uvloop
from aiogram import Bot

from src.bot.api import get_keyboard
from src.bot import keyboards
from src.utils import config


class TelegramAPI(Bot):
    def __init__(self, **kwargs):
        if 'token' not in kwargs:
            kwargs.update({'token': config['tesseract']['token-iro-mega-bot']})
        super().__init__(**kwargs)

    def __del__(self):
        asyncio.ensure_future(self._close())

    async def _close(self):
        await self.session.close()


# __loop = asyncio.new_event_loop()
__loop = uvloop.new_event_loop()
asyncio.set_event_loop(__loop)
telegram_api = TelegramAPI()
