import logging

from aiogram import Bot
from aiogram.utils import exceptions

from src.bot.api import get_keyboard
from src.bot import keyboards
from src.text import Texts
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


async def send_message(chat_id: int, text: str, *args, **kwargs):
    log = logging.getLogger('irobot-web')
    try:
        res = await telegram_api.send_message(chat_id, text, *args, **kwargs)
    except exceptions.BotBlocked:
        log.error(f"Blocked by user [{chat_id}]")
    except exceptions.ChatNotFound:
        log.error(f"Invalid user ID [{chat_id}]")
    except exceptions.RetryAfter as e:
        log.error(f"Flood limit is exceeded. Sleep {e.timeout} seconds [{chat_id}]")
        await asyncio.sleep(e.timeout)
        return await send_message(chat_id, text, *args, **kwargs)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"User is deactivated [{chat_id}]")
    except exceptions.TelegramAPIError:
        log.exception(f"Failed [{chat_id}]")
    else:
        return res
    return False


async def send_feedback(chat_id, task_id):
    res = await send_message(chat_id, Texts.new_feedback, Texts.new_feedback.parse_mode,
                             reply_markup=get_keyboard(keyboards.get_feedback_btn(task_id), row_size=5))
    if res:
        await sql.upd_inline(chat_id, res.message_id, Texts.new_feedback, Texts.new_feedback.parse_mode)
    return res


async def delete_message(chat_id, message_id):
    try:
        await telegram_api.delete_message(chat_id, message_id)
    except:
        pass


async def edit_message_text(text, chat_id, message_id, *args, **kwargs):
    log = logging.getLogger('irobot-web')
    res = False
    try:
        res = await telegram_api.edit_message_text(text, chat_id, message_id, *args, **kwargs)
    except exceptions.RetryAfter as e:
        log.error(f'Flood limit is exceeded. Sleep {e.timeout} seconds.')
        await asyncio.sleep(e.timeout)
        return await send_message(chat_id, text, *args, **kwargs)  # Recursive call
    except:
        await delete_message(chat_id, message_id)
        res = await send_message(chat_id, text, *args, **kwargs)
    finally:
        return res


async def edit_inline_message(chat_id, text, *args, **kwargs):
    inline_msg_id, _, _ = await sql.get_inline(chat_id)
    if inline_msg_id:
        await edit_message_text(text, chat_id, inline_msg_id, *args, **kwargs)
    else:
        await send_message(chat_id, text, *args, **kwargs)


async def send_chat_action(chat_id, action):
    try:
        await telegram_api.send_chat_action(chat_id, action)
    except:
        pass


telegram_api = TelegramAPI()
