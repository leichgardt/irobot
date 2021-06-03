import typing

from aiogram import Bot, types
from aiogram.utils.exceptions import MessageNotModified, BadRequest
from aiogram.dispatcher import FSMContext

from src.sql import sql
from src.bot.bot_core import bot
from src.bot import keyboards
from src.bot.text import Texts
from src.bot.api.bot_keyboard_master import get_keyboard
from src.utils import alogger


def private_and_login_require(do_not_check_sub=False):
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
                                               dict]):
    try:
        if isinstance(message, (tuple, list, dict)):
            if isinstance(message, (tuple, list)):
                chat_id = message[0]
                message_id = message[1]
            else:
                chat_id = message['chat_id']
                message_id = message['message_id']
            await bot.delete_message(chat_id, message_id)
        else:
            await message.delete()
    except:
        pass


async def clear_inline_message(bot, chat_id):
    inline, text, parse_mode = await sql.get_inline(chat_id)
    if inline and text:
        try:
            await bot.edit_message_text(text, chat_id, inline, parse_mode=parse_mode)
        except (MessageNotModified, BadRequest):
            await sql.upd_inline(chat_id, 0, '')


async def edit_inline_message(bot: Bot,
                              chat_id: int,
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
            await bot.edit_message_text(text, chat_id, inline, reply_markup=reply_markup, parse_mode=parse_mode,
                                        disable_web_page_preview=disable_web_page_preview)
            await sql.upd_inline(chat_id, inline, text, parse_mode)
        except (MessageNotModified, BadRequest):
            res = await bot.send_message(chat_id, text, parse_mode, disable_web_page_preview=disable_web_page_preview,
                                         reply_markup=reply_markup)
            await delete_message((chat_id, inline))
            await sql.upd_inline(chat_id, res.message_id, text, parse_mode)
        except Exception as e:
            await alogger.warning(e)
            await sql.upd_inline(chat_id, 0, '')
    return inline


async def update_inline_query(
        bot: Bot,
        query: types.CallbackQuery,
        answer: str,
        text: str = None,
        parse_mode: str = None,
        title: str = None,
        alert: bool = False,
        btn_list: list = None,
        keyboard: types.InlineKeyboardMarkup = None, ):
    if btn_list:
        keyboard = get_keyboard(*btn_list, keyboard_type='inline')
    text = f'{title}\n\n{text}' if title else text
    try:
        await bot.edit_message_text(text, query.message.chat.id, query.message.message_id,
                                    reply_markup=keyboard, parse_mode=parse_mode)
    except (MessageNotModified, BadRequest):
        await delete_message(query.message)
        await bot.send_message(query.message.chat.id, text, parse_mode, reply_markup=keyboard)
    else:
        await query.answer(answer, show_alert=alert)
        await sql.upd_inline(query.message.chat.id, query.message.message_id, query.message.text, parse_mode=parse_mode)


main_menu = get_keyboard(keyboards.main_menu_btn, keyboard_type='reply', one_time_keyboard=True)
cancel_menu = {'inline': get_keyboard(keyboards.cancel_btn, keyboard_type='inline'),
               'reply': get_keyboard(keyboards.cancel_btn, keyboard_type='reply', one_time_keyboard=True)}
