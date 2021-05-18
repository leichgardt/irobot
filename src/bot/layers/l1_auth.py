import hashlib

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, StateFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.utils import logger
from src.sql import sql
from src.lb import check_account_pass
from src.bot.api import main_menu, clear_inline_message, cancel_menu, get_keyboard_menu, edit_inline_message, \
    get_reply_keyboard_menu, update_inline_query
try:
    from .l0_test import bot, dp
except ImportError:
    from src.bot.bot_core import bot, dp


class AuthFSM(StatesGroup):
    # конечный автомат, последовательное заполнение agrm и pwd, чтобы потом с ними авторизоваться в биллинге
    agrm = State()
    pwd = State()


@dp.callback_query_handler(text='cancel', state=AuthFSM.agrm)
@dp.callback_query_handler(text='cancel', state=AuthFSM.pwd)
async def inline_cb_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(agrm='', pwd='')
    await AuthFSM.agrm.set()
    await update_inline_query(bot, query, 'Начало', text='Отправь /start чтобы начать.')


@dp.message_handler(commands='start', state='*')
async def start_cmd_h(message: types.Message, state: FSMContext):
    await state.finish()
    await clear_inline_message(bot, message.chat.id)
    if await sql.get_sub(message.from_user.id):
        # показать главное меню (баланс, оплата, тариф, настройки)
        res = await bot.send_message(message.chat.id, main_menu[0], reply_markup=main_menu[1], parse_mode=main_menu[2])
        # await bot.pin_chat_message(message.chat.id, res.message_id, True)
        await sql.upd_inline(message.chat.id, res.message_id, res.text)
    else:
        # авторизация
        await AuthFSM.agrm.set()  # запуск конечного автомата
        logger.info(f'Start [{message.chat.id}]')
        name = message.from_user.first_name
        text = f'Привет, {name}!\nС помощью этого бота ты сможешь проверять и пополнять баланс, менять тарифы и ' \
               f'многое другое!\n\nНо сначала давай авторизуемся!\n\n<u>Напиши номер договора</u>.'
        res = await bot.send_message(message.chat.id, text, reply_markup=cancel_menu[1], parse_mode=types.ParseMode.HTML)
        await sql.add_chat(message.chat.id, res.message_id, text, parse_mode=types.ParseMode.HTML)


@dp.message_handler(state=AuthFSM.agrm)
async def fsm_auth_agrm_h(message: types.Message, state: FSMContext):
    logger.info(f'Getting agrm [{message.chat.id}]')
    async with state.proxy() as data:
        await AuthFSM.next()
        data['agrm'] = message.text
        text = f'Договор: {message.text}\nВведи пароль. Не волнуйся, его не будет видно в истории чата :sunglasses:'
        await edit_inline_message(bot, message.chat.id, emojize(text), reply_markup=cancel_menu[1])
        await message.delete()


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


@dp.message_handler(state=AuthFSM.pwd)
async def fsm_auth_pwd_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        logger.info(f'Getting password [{message.chat.id}]')
        data['pwd'] = message.text
        await message.delete()
        pwd_check, agrm_id = await check_account_pass(data['agrm'], data['pwd'])
        if pwd_check == 1:
            await state.finish()
            logger.info(f'Logged [{message.chat.id}]')
            await sql.subscribe(message.chat.id)
            await sql.add_agrm(message.chat.id, data['agrm'], agrm_id)
            text = f'Ты успешно авторизовался под договором {data["agrm"]} :tada:\nДобро пожаловать! :smile:\n\n'
            text = emojize(text) + main_menu[0].split('\n\n')[-1]
            await bot.send_message(message.chat.id, text, reply_markup=main_menu[1])
            # inline = await edit_inline_message(bot, message.chat.id, text, reply_markup=main_menu[1])
            # await bot.pin_chat_message(message.chat.id, inline, True)
        elif pwd_check == 0:
            await AuthFSM.agrm.set()
            text = 'Неправильный номер договора или пароль. Попробуй еще раз!\n\nВведи номер договора.'
            await edit_inline_message(bot, message.chat.id, text, reply_markup=cancel_menu[1])
        else:
            await AuthFSM.agrm.set()
            text = 'Ошибка! Договор не найден.\nПопробуй ввести номер другого договора.'
            await edit_inline_message(bot, message.chat.id, text, reply_markup=cancel_menu[1])
        data['pwd'] = ''


@dp.message_handler(commands='cancel', state=AuthFSM.agrm)
@dp.message_handler(commands='cancel', state=AuthFSM.pwd)
async def cancel_cmd_h(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    logger.info(f'Cancelling [{message.chat.id}]')
    text, kb = await get_reply_keyboard_menu('start')
    text = 'Отменено. ' + text
    await edit_inline_message(bot, message.chat.id, text, reply_markup=kb)


# @dp.message_handler(commands=('logout', 'exit', 'stop'))
# @dp.message_handler(Text(equals=('logout', 'exit', 'stop'), ignore_case=True))
# async def logout_cmd_h(message: types.Message):
#     if await sql.get_sub(message.chat.id):
#         await sql.unsubscribe(message.chat.id)
#         agrms = sql.get_agrms(message.chat.id)
#         for agrm in agrms:
#             await sql.del_agrm(message.chat.id, agrm)
#         text = 'Ты успешно вышел из учётных записей.'
#         await bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
#     else:
#         text = 'Ты не авторизован. Чтобы авторизоваться, отправь /auth'
#         await bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
