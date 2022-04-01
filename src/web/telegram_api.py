import aiohttp
import asyncio
import logging

from aiogram import Bot
from aiogram.utils import exceptions

from src.bot import keyboards
from src.bot.api.keyboard import Keyboard
from src.parameters import API_TOKEN
from src.text import Texts
from src.run_bot import WEBAPP_PORT
from src.sql import sql


__all__ = (
    'telegram_api',
    'send_message',
    'send_feedback',
    'edit_message_text',
    'webhook_request',
    'edit_inline_message',
    'delete_message',
    'send_chat_action',
    'get_profile_photo'
)


class TelegramAPI(Bot):
    def __init__(self, **kwargs):
        if 'token' not in kwargs:
            kwargs.update({'token': API_TOKEN})
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
                             reply_markup=Keyboard(keyboards.get_feedback_btn(task_id), row_size=5).inline())
    if res:
        await sql.upd_inline_message(chat_id, res.message_id, Texts.new_feedback, Texts.new_feedback.parse_mode)
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
    inline_msg_id, _, _ = await sql.get_inline_message(chat_id)
    if inline_msg_id:
        await edit_message_text(text, chat_id, inline_msg_id, *args, **kwargs)
    else:
        await send_message(chat_id, text, *args, **kwargs)


async def send_chat_action(chat_id, action):
    try:
        await telegram_api.send_chat_action(chat_id, action)
    except:
        pass


async def webhook_request(data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://localhost:{WEBAPP_PORT}/', json=data) as res:
            try:
                return await res.json()
            except aiohttp.client_exceptions.ContentTypeError:
                return {'ok': True}


async def get_profile_photo(chat_id):
    try:
        res = await telegram_api.get_user_profile_photos(chat_id, limit=1)
    except:
        pass
    else:
        if res['total_count']:
            file = await telegram_api.get_file(res['photos'][0][0]['file_id'])
            return telegram_api.get_file_url(file['file_path'])


telegram_api = TelegramAPI()


if __name__ == '__main__':
    async def main():
        res = await telegram_api.send_message(config['irobot']['me'], 'lmao')
        print(res)

    asyncio.run(main())
