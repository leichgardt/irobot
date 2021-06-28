import asyncio
from aiogram import Bot
from aiogram.utils import exceptions
import logging

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


async def send_message(chat_id: int, text: str, *args, **kwargs):
    log = logging.getLogger('irobot-web')
    try:
        res = await telegram_api.send_message(chat_id, text, *args, **kwargs)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{chat_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{chat_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(chat_id, text, *args, **kwargs)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{chat_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{chat_id}]: failed")
    else:
        return res
    return False


async def send_feedback(chat_id, task_id):
    res = await send_message(chat_id, Texts.new_feedback, Texts.new_feedback.parse_mode,
                             reply_markup=get_keyboard(keyboards.get_feedback_btn(task_id), row_size=5))
    if res:
        await sql.upd_inline(chat_id, res.message_id, Texts.new_feedback, Texts.new_feedback.parse_mode)
    return res


telegram_api = TelegramAPI()
