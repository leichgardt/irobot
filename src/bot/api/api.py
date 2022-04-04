import asyncio
import typing
from functools import wraps

from aiogram import types, exceptions
from aiogram.dispatcher import FSMContext

from src.sql import sql
from src.bot.core import bot
from src.bot.api.keyboard import Keyboard
from src.text import Texts
from src.utils import logger


__all__ = ('exc_handler', 'private_and_login_require', 'delete_message', 'edit_inline_message', 'update_inline_query')


def exc_handler(func: typing.Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        bot_func = func.__name__
        try:
            return await func(*args, **kwargs)
        except exceptions.BotBlocked:
            await logger.error(f'{bot_func}: Blocked by user {args}')
        except exceptions.ChatNotFound:
            await logger.error(f'{bot_func}: Chat ID not found {args}')
        except exceptions.RetryAfter as e:
            await logger.error(f'{bot_func}: Flood limit is exceeded, sleep {e.timeout} seconds {args}')
            await asyncio.sleep(e.timeout)
            return await func(*args, **kwargs)  # Recursive call
        except exceptions.UserDeactivated:
            await logger.error(f'{bot_func}: User is deactivated {args}')
        except Exception as e:
            chat_id, state_data = '', ''
            if args:
                msg = [arg for arg in args if isinstance(arg, (types.Message, types.CallbackQuery))]
                if msg:
                    try:
                        if isinstance(msg[0], types.Message):
                            chat_id = msg[0].chat.id
                            await bot.send_message(msg[0].chat.id, *Texts.backend_error.pair())
                        elif isinstance(msg[0], types.CallbackQuery):
                            chat_id = msg[0].message.chat.id
                            await msg[0].answer(Texts.backend_error, show_alert=True)
                    except:
                        pass
                state = [arg for arg in args if isinstance(arg, FSMContext)]
                if state:
                    with await state[0].proxy() as data:
                        state_data = str(data)
            await logger.exception(f'{bot_func}: {e}'
                                   + (f' [{chat_id}]' if chat_id else '')
                                   + (f' ({state_data})' if state_data else ''))
    return wrapper


def private_and_login_require(do_not_check_sub=False):
    """
    do_not_check_sub - Передайте True, чтобы разрешать неавторизованным пользователям доступ к декорируемой функции
    """

    def decorator(func: typing.Callable):
        async def message_handler(message: types.Message, state: FSMContext):
            if message.chat.type == 'private':
                if do_not_check_sub:
                    return await func(message, state)
                if await sql.get_sub(message.chat.id):
                    return await func(message, state)
                await message.reply(Texts.non_auth, Texts.non_auth.parse_mode)
            else:
                await message.reply(Texts.non_private, Texts.non_auth.parse_mode)

        return message_handler

    return decorator


async def delete_message(message: typing.Union[types.Message, tuple, list, dict, int]):
    try:
        if isinstance(message, (tuple, list, dict, int)):
            if isinstance(message, int):
                chat_id = message
                message_id, _, _ = await sql.get_inline_message(chat_id)
            elif isinstance(message, (tuple, list)):
                chat_id = message[0]
                message_id = message[1]
            else:
                chat_id = message['chat_id']
                message_id = message['message_id']
            if chat_id and message_id:
                await bot.delete_message(chat_id, message_id)
        else:
            await message.delete()
    except:
        pass


async def edit_inline_message(
        chat_id: int,
        text: str,
        parse_mode: str = None,
        reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                   types.ReplyKeyboardMarkup,
                                   types.ReplyKeyboardRemove] = None,
        message_id: int = None,
        disable_web_page_preview: bool = False,
        btn_list: list = None
):
    if message_id is None:
        message_id, _, _ = await sql.get_inline_message(chat_id)
    if not reply_markup and btn_list:
        if not isinstance(btn_list, (list, tuple, set)):
            btn_list = [btn_list]
        reply_markup = Keyboard(btn_list).inline()
    if message_id:
        if reply_markup and isinstance(reply_markup, (types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove)):
            await resend_inline_message(chat_id, message_id, text, parse_mode, reply_markup=reply_markup,
                                        disable_web_page_preview=disable_web_page_preview)
        else:
            await try_to_edit_inline_message(chat_id, message_id, text, parse_mode, reply_markup,
                                             disable_web_page_preview)


async def try_to_edit_inline_message(chat_id, message_id, text, parse_mode, reply_markup, disable_web_page_preview):
    try:
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode,
                                    disable_web_page_preview=disable_web_page_preview)
    except (exceptions.MessageNotModified,
            exceptions.BadRequest,
            exceptions.InlineKeyboardExpected,
            exceptions.TelegramAPIError):
        await resend_inline_message(chat_id, message_id, text, parse_mode, reply_markup=reply_markup,
                                    disable_web_page_preview=disable_web_page_preview)
    except Exception as e:
        await logger.warning(e)
        await sql.upd_inline_message(chat_id, 0, '')
    else:
        await sql.upd_inline_message(chat_id, message_id, text, parse_mode)


async def update_inline_query(
        query: types.CallbackQuery,
        answer: str,
        text: str = None,
        parse_mode: str = None,
        alert: bool = False,
        btn_list: list = None,
        reply_markup: types.InlineKeyboardMarkup = None,
        skip_db_update: bool = False
):
    """
    Используйте, когда нужно обработать нажатие query inline-кнопки у сообщения для изменения содержания этого сообщения

    :param query: Объект запроса
    :param answer: Текст ответа на запрос
    :param text: Новый текст сообщения
    :param parse_mode: Метод парсинга текста сообщения
    :param alert: Передайте True, чтобы ответ на запрос появился в отдельном окошке
    :param btn_list: Список кнопок inline клавиатуры, которые собирутся в клавиатуру
    :param reply_markup: Клавиатура
    :param skip_db_update: Пропустить обновление БД
    """
    if btn_list:
        reply_markup = Keyboard(btn_list).inline()
    try:
        await bot.edit_message_text(text, query.message.chat.id, query.message.message_id,
                                    reply_markup=reply_markup, parse_mode=parse_mode)
    except (exceptions.MessageNotModified, exceptions.BadRequest,
            exceptions.InlineKeyboardExpected, exceptions.TelegramAPIError):
        await resend_inline_message(query.message.chat.id, query.message.message_id, text, parse_mode,
                                    reply_markup=reply_markup, skip_db_update=True)
    else:
        await query.answer(answer, show_alert=alert)
        if not skip_db_update:
            await sql.upd_inline_message(query.message.chat.id, query.message.message_id, text, parse_mode=parse_mode)


async def resend_inline_message(chat_id, message_id, text, parse_mode, skip_db_update=False, **kwargs):
    await delete_message((chat_id, message_id))
    res = await bot.send_message(chat_id, text, parse_mode, **kwargs)
    if not skip_db_update:
        await sql.upd_inline_message(chat_id, res.message_id, text, parse_mode)
