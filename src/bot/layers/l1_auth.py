from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.utils import alogger
from src.sql import sql
from src.lb import check_account_pass
from src.bot.api import main_menu, cancel_menu, update_inline_query, edit_inline_message, delete_message, private_and_login_require
from src.bot.text import Texts

try:
    from .l0_test import bot, dp
except ImportError:
    from src.bot.bot_core import bot, dp


async def is_cancel(message: types.Message):
    if message.text[0] == '/' or message.text.lower() in ['cancel', 'back', 'отмена', 'назад']:
        await bot.send_message(message.chat.id, Texts.auth_cancel, Texts.auth_cancel.parse_mode)
        await alogger.info(f'Cancelling [{message.chat.id}]')
        return True
    return False


class AuthFSM(StatesGroup):
    # конечный автомат, последовательное заполнение agrm и pwd, чтобы потом с ними авторизоваться в биллинге
    agrm = State()
    pwd = State()


@dp.message_handler(Text('старт', ignore_case=True), state='*')
@dp.message_handler(commands='start', state='*')
@private_and_login_require(do_not_check_sub=True)
async def start_cmd_h(message: types.Message, state: FSMContext):
    await state.finish()
    if await sql.get_sub(message.from_user.id):
        await bot.send_message(message.chat.id, text=Texts.main_menu, parse_mode=Texts.main_menu.parse_mode,
                               reply_markup=main_menu)
    else:
        await AuthFSM.agrm.set()  # запуск конечного автомата - авторизация
        await alogger.info(f'Start [{message.chat.id}]')
        text = Texts.start.format(name=message.from_user.first_name)
        res = await bot.send_message(message.chat.id, text, parse_mode=Texts.start.parse_mode,
                                     reply_markup=cancel_menu['inline'])
        await sql.add_chat(message.chat.id, res.message_id, text, parse_mode=Texts.start.parse_mode)


@dp.message_handler(state=AuthFSM.agrm)
async def fsm_auth_agrm_h(message: types.Message, state: FSMContext):
    await alogger.info(f'Getting agrm [{message.chat.id}]')
    async with state.proxy() as data:
        if await is_cancel(message):
            await state.finish()
            return
        await AuthFSM.next()
        data['agrm'] = message.text
        text = Texts.auth_pwd.format(agrm=data['agrm'])
        res = await bot.send_message(message.chat.id, text, parse_mode=Texts.auth_pwd.parse_mode,
                                     reply_markup=cancel_menu['inline'])
        await sql.upd_inline(message.chat.id, res.message_id, res.text, Texts.auth_pwd.parse_mode)


@dp.message_handler(state=AuthFSM.pwd)
async def fsm_auth_pwd_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if await is_cancel(message):
            await state.finish()
            return
        data['pwd'] = message.text
        await delete_message(message)
        await alogger.info(f'Getting password [{message.chat.id}]')
        pwd_check, agrm_id = await check_account_pass(data['agrm'], data['pwd'])
        if pwd_check == 1:
            await alogger.info(f'Logged [{message.chat.id}]')
            await sql.subscribe(message.chat.id)
            await sql.add_agrm(message.chat.id, data['agrm'], agrm_id)
            await state.finish()
            text = Texts.auth_success.format(agrm=data['agrm'])
            await edit_inline_message(bot, message.chat.id, text, Texts.auth_success.parse_mode)
            await bot.send_message(message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode, reply_markup=main_menu)
            await sql.upd_inline(message.chat.id, 0, '', '')
        elif pwd_check == 0:
            await AuthFSM.agrm.set()
            await bot.send_message(message.chat.id, Texts.auth_fail, reply_markup=cancel_menu['inline'])
        else:
            await AuthFSM.agrm.set()
            await bot.send_message(message.chat.id, Texts.auth_error, reply_markup=cancel_menu['inline'])
        data['pwd'] = ''


@dp.callback_query_handler(text='cancel', state=[AuthFSM.agrm, AuthFSM.pwd])
async def inline_cb_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(bot, query, *Texts.auth_cancel.full())

# @dp.inline_handler(state=AuthFSM.pwd)
# async def fsm_auth_inline_pwd_h(inline_query: types.InlineQuery, state: FSMContext):
#     st = await state.get_state()
#     print('state', type(st), st)
#     async with state.proxy() as data:
#         pwd = inline_query.query
#         data['pwd'] = pwd  # запоминаем пароль
#         if pwd:
#             text = f'Ввести пароль {pwd!r}'
#             stars = 'Пароль: ' + ('*****' * (len(pwd) // 5 + 1)) + ('*****' if len(pwd) // 5 == 0 else '')
#             input_content = types.InputTextMessageContent(stars[:23])
#         else:
#             text = 'Введите пароль.'
#             input_content = types.InputTextMessageContent('Вы не ввели пароль.')
#         result_id: str = hashlib.md5(text.encode()).hexdigest()
#         item = types.InlineQueryResultArticle(
#             id=result_id,
#             title=text,
#             input_message_content=input_content,
#         )
#         await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
