from aiogram import Bot, types
from aiogram.utils.exceptions import MessageNotModified, BadRequest
from asyncio import get_event_loop

from src.sql import sql
from src.bot.api.keyboards import get_keyboard_menu
from src.utils import logger


async def clear_inline_message(bot, chat_id):
    inline, text, parse_mode = await sql.get_inline(chat_id)
    if inline and text:
        try:
            await bot.edit_message_text(text, chat_id, inline, parse_mode=parse_mode)
        except (MessageNotModified, BadRequest):
            await sql.upd_inline(chat_id, 0, '')


async def edit_inline_message(bot, chat_id, text, reply_markup=None, parse_mode=None):
    inline, _, _ = await sql.get_inline(chat_id)
    if inline:
        try:
            await bot.edit_message_text(text, chat_id, inline, reply_markup=reply_markup, parse_mode=parse_mode)
        except (MessageNotModified, BadRequest):
            await sql.upd_inline(chat_id, 0, '')
        except Exception as e:
            logger.warning(e)
            await sql.upd_inline(chat_id, 0, '')
        else:
            await sql.upd_inline(chat_id, inline, text, parse_mode=parse_mode)
    return inline


async def update_inline_query(
        bot: Bot,
        query: types.CallbackQuery,
        answer: str,
        menu: str = None,
        alert=False,
        text=None,
        title=None,
        keyboard=None,
        parse_mode=None):
    if menu:
        text, keyboard, parse_mode = await get_keyboard_menu(menu, query.message.chat.id, title=title)
    try:
        res = await bot.edit_message_text(text, query.message.chat.id, query.message.message_id, reply_markup=keyboard,
                                          parse_mode=parse_mode)
    except (MessageNotModified, BadRequest):
        pass
    else:
        await query.answer(answer, show_alert=alert)
        await sql.upd_inline(query.message.chat.id, res.message_id, res.text, parse_mode=parse_mode)


class Menu:
    def __init__(self):
        self._loop = get_event_loop()
        self.main_menu = self._loop.run_until_complete(get_keyboard_menu('main'))
        self.cancel_menu = self._loop.run_until_complete(get_keyboard_menu('cancel'))

    def get_menus(self):
        return self.main_menu, self.cancel_menu


main_menu, cancel_menu = Menu().get_menus()
