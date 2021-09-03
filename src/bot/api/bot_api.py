import asyncio
import typing

from aiogram import types, exceptions
from aiogram.dispatcher import FSMContext

from src.sql import sql
from src.bot.bot_core import bot
from src.bot import keyboards
from src.bot.text import Texts
from src.bot.api.bot_keyboard_master import get_keyboard
from src.utils import alogger


async def run_cmd(bot_func: [asyncio.coroutines, asyncio.tasks]):
    """
    Функция-обработчик методов бота.
    Используйте для всех методов бота, чтобы обрабатывать и логировать исключения

    :param bot_func: Сопрограмма или задание от бота в асинхронном виде. Вместо
        >>> await bot.send_message(...)
        используйте
        >>> await run_cmd(bot.send_message(...))

    :return В случае успеха возвращает результат сопрограммы/задания, иначе False
    """
    task = asyncio.create_task(bot_func)
    args = bot_func.cr_frame.f_locals
    if 'self' in args:
        args.pop('self')
    try:
        return await task
    except exceptions.BotBlocked:
        await alogger.error(f'{bot_func.__qualname__}: Blocked by user {args}')
    except exceptions.ChatNotFound:
        await alogger.error(f'{bot_func.__qualname__}: Chat ID not found {args}')
    except exceptions.RetryAfter as e:
        await alogger.error(f'{bot_func.__qualname__}: Flood limit is exceeded, sleep {e.timeout} seconds {args}')
        await asyncio.sleep(e.timeout)
        return await task  # Recursive call
    except exceptions.UserDeactivated:
        await alogger.error(f'{bot_func.__qualname__}: User is deactivated {args}')
    except Exception as e:
        raise e
    return False


def private_and_login_require(do_not_check_sub: bool = False):
    """
    Декоратор-ограничитель, который блокирует функции для неавторизованных пользователей и публичных чатов

    :param do_not_check_sub: Передайте True, чтобы разрешать функции неавторизованным пользователям
    """
    def decorator(func):
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


async def delete_message(message: typing.Union[types.Message,
                                               tuple,
                                               list,
                                               dict,
                                               int]):
    """
    Удалить сообщение

    :param message: указатель на сообщение
    :type message: :obj:`types.Message` - объект класса сообщения
    :type message: :tuple: :list: :dict: - указывается chat_id и message_id
    :type message: :int: - chat_id; в этом случае удаляется сообщение inline, загружаемое с БД
    """
    try:
        if isinstance(message, (tuple, list, dict, int)):
            if isinstance(message, int):
                chat_id = message
                message_id, _, _ = await sql.get_inline(chat_id)
            elif isinstance(message, (tuple, list)):
                chat_id = message[0]
                message_id = message[1]
            else:
                chat_id = message['chat_id']
                message_id = message['message_id']
            if chat_id and message_id:
                await run_cmd(bot.delete_message(chat_id, message_id))
        else:
            await run_cmd(message.delete())
    except:
        pass


async def clear_inline_message(chat_id: int):
    inline, text, parse_mode = await sql.get_inline(chat_id)
    if inline and text:
        try:
            await run_cmd(bot.edit_message_text(text, chat_id, inline, parse_mode=parse_mode))
        except (exceptions.MessageNotModified, exceptions.BadRequest):
            await sql.upd_inline(chat_id, 0, '')


async def edit_inline_message(chat_id: int,
                              text: str,
                              parse_mode: str = None,
                              reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                         types.ReplyKeyboardMarkup,
                                                         types.ReplyKeyboardRemove,
                                                         None] = None,
                              inline: int = None,
                              disable_web_page_preview: bool = False):
    if inline is None:
        inline, _, _ = await sql.get_inline(chat_id)
    if inline:
        try:
            await run_cmd(bot.edit_message_text(text, chat_id, inline, reply_markup=reply_markup, parse_mode=parse_mode,
                                                disable_web_page_preview=disable_web_page_preview))
        except (exceptions.MessageNotModified, exceptions.BadRequest,
                exceptions.InlineKeyboardExpected, exceptions.TelegramAPIError):
            await delete_message((chat_id, inline))
            res = await run_cmd(bot.send_message(chat_id, text, parse_mode, reply_markup=reply_markup,
                                                 disable_web_page_preview=disable_web_page_preview))
            await sql.upd_inline(chat_id, res.message_id, text, parse_mode)
        except Exception as e:
            await alogger.warning(e)
            await sql.upd_inline(chat_id, 0, '')
        else:
            await sql.upd_inline(chat_id, inline, text, parse_mode)
    return inline


async def update_inline_query(
        query: types.CallbackQuery,
        answer: str,
        text: str = None,
        parse_mode: str = None,
        title: str = None,
        alert: bool = False,
        btn_list: list = None,
        reply_markup: types.InlineKeyboardMarkup = None):
    """
    Обновить inline query сообщение, его текст, клавиатуру и т.д., а так же вызвать Ответ на этот inline запрос.
    Используйте, когда нужно обработать нажатие inline кнопки сообщения для изменения содержания этого сообщения.

    :param query: Объект запроса
    :param answer: Текст ответа на запрос
    :param text: Новый текст сообщения
    :param parse_mode: Метод парсинга текста сообщения
    :param title: -не используется-
    :param alert: Передайте True, чтобы ответ на запрос появился в отдельном окошке
    :param btn_list: Список кнопок inline клавиатуры, которые собирутся в клавиатуру
    :param reply_markup: Клавиатура
    """
    if btn_list:
        reply_markup = get_keyboard(*btn_list, keyboard_type='inline')
    text = f'{title}\n\n{text}' if title else text
    try:
        await run_cmd(bot.edit_message_text(text, query.message.chat.id, query.message.message_id,
                                            reply_markup=reply_markup, parse_mode=parse_mode))
    except (exceptions.MessageNotModified, exceptions.BadRequest,
            exceptions.InlineKeyboardExpected, exceptions.TelegramAPIError):
        await delete_message(query.message)
        await run_cmd(bot.send_message(query.message.chat.id, text, parse_mode, reply_markup=reply_markup))
    else:
        await query.answer(answer, show_alert=alert)
        await sql.upd_inline(query.message.chat.id, query.message.message_id, text, parse_mode=parse_mode)


main_menu = get_keyboard(keyboards.main_menu_btn, keyboard_type='reply', one_time_keyboard=True)
cancel_menu = {'inline': get_keyboard(keyboards.cancel_btn, keyboard_type='inline'),
               'reply': get_keyboard(keyboards.cancel_btn, keyboard_type='reply', one_time_keyboard=True)}
