import hashlib
import asyncio

from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, StateFilter, RegexpCommandsFilter, Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.utils import logger
from src.sql import sql
from src.lb import check_account_pass
from src.bot.api import main_menu, clear_inline_message, get_keyboard_menu, update_inline_query, edit_inline_message, cancel_menu
from .l1_auth import bot, dp


@dp.message_handler(commands='settings', state='*')
async def message_h_settings(message: types.Message, state: FSMContext):
    await state.finish()
    text, kb, parse = await get_keyboard_menu('settings')
    if not await sql.get_sub(message.chat.id):
        kb = None
        text = 'Чтобы настраивать бота, тебе надо авторизоваться, отправив команду /start'
    await clear_inline_message(bot, message.chat.id)
    res = await bot.send_message(message.chat.id, text, parse_mode=parse, reply_markup=kb)
    await sql.upd_inline(message.chat.id, res.message_id, text, parse)


@dp.callback_query_handler(text='settings', state='*')
async def inline_cb_h_settings(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(bot, query, 'Настройки', 'settings')
    await AgrmSettingsFSM.agrm.set()


@dp.callback_query_handler(text='settings-done', state='*')
async def inline_cb_h_settings_complete(query: types.CallbackQuery, state: FSMContext):
    logger.info(f'New settings accepted [{query.from_user.id}]')
    text, kb, parse_mode = main_menu
    await query.answer('Настройки сохранены', show_alert=True)
    res = await query.message.edit_text(text, reply_markup=kb, parse_mode=parse_mode)
    await sql.upd_inline(query.message.chat.id, res.message_id, res.text)
    await state.finish()


class AgrmSettingsFSM(StatesGroup):
    agrm = State()
    pwd = State()


# @dp.callback_query_handler(text='cancel', state='*')
# async def inline_cb_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
#     await state.finish()
#     is_sub = await sql.get_sub(query.message.chat.id)
#     if is_sub:
#         await update_inline_query(bot, query, 'Главное меню', 'main-menu')
#     else:
#         name = query.from_user.first_name
#         text = f'Привет, {name}!\nОтправь /start и мы начнем!'
#         await update_inline_query(bot, query, 'Начало', text=text)


@dp.callback_query_handler(text='cancel', state=AgrmSettingsFSM.agrm)
@dp.callback_query_handler(text='cancel', state=AgrmSettingsFSM.pwd)
async def inline_cb_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(agrm='', pwd='')
    await AgrmSettingsFSM.agrm.set()
    await update_inline_query(bot, query, 'Настройки договоров', 'agrms')


@dp.callback_query_handler(text='settings-my-agrms', state='*')
async def inline_cb_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(bot, query, 'Настройки договоров', 'agrms')
    await AgrmSettingsFSM.agrm.set()


@dp.callback_query_handler(Regexp(regexp=r'agrm-(?!del)(?!del-yes)(?!del-no)(?!add)([^\s]*)'),
                           state=AgrmSettingsFSM.agrm)
async def inline_cb_h_agrm_control(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        agrm = query.data[5:]
        data['agrm'] = agrm
        text, kb, parse_mode = await get_keyboard_menu('agrm', query.message.chat.id)
        text = f'Настройки >> Договоры >> {agrm}\n\n' + text
        await update_inline_query(bot, query, f'Выбран договор {agrm}', text=text, keyboard=kb, parse_mode=parse_mode)


@dp.callback_query_handler(text='agrm-del', state=AgrmSettingsFSM.agrm)
async def inline_cb_h_agrm_del(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        logger.info(f'Agrm {data["agrms"]} deleted [{query.message.chat.id}]')
        await state.finish()
        await AgrmSettingsFSM.agrm.set()
        await sql.del_agrm(query.message.chat.id, data['agrm'])
        await update_inline_query(bot, query, f'Договор {data["agrm"]} удалён', 'agrms', alert=True)


@dp.callback_query_handler(text='agrm-add', state=AgrmSettingsFSM.agrm)
async def inline_cb_h_agrm_del(query: types.CallbackQuery, state: FSMContext):
    logger.info(f'Agrm adding [{query.message.chat.id}]')
    await state.finish()
    await AgrmSettingsFSM.agrm.set()
    text = f'Настройки >> Договоры >> Добавить\n\nВведи номер договора.'
    await update_inline_query(bot, query, f'Добавить новый договор', text=text, keyboard=cancel_menu[1])


@dp.message_handler(state=AgrmSettingsFSM.agrm)
async def fsm_auth_agrm_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['agrm'] = message.text
        chat_id = message.chat.id
        text = f'Настройки >> Договоры >> Добавить\n\nНомер договора: {data["agrm"]} \nВведи пароль.'
        await AgrmSettingsFSM.next()
        await message.delete()
        await edit_inline_message(bot, chat_id, text, reply_markup=cancel_menu[1])


@dp.message_handler(state=AgrmSettingsFSM.pwd)
async def fsm_auth_pwd_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['pwd'] = message.text
        chat_id = message.chat.id
        await message.delete()
        pwd_check, agrm_id = await check_account_pass(data['agrm'], data['pwd'])
        if pwd_check == 1:
            logger.info(f'Agrm {data["agrms"]} was added [{message.chat.id}]')
            await sql.add_agrm(message.chat.id, data['agrm'], agrm_id)
            text, kb, parse_mode = await get_keyboard_menu('agrms', message.chat.id)
            text = text.split('\n\n')
            text = text[0] + emojize(f'\n\nДоговор {data["agrm"]} успешно добавлен :tada:\n') + text[1]
            await edit_inline_message(bot, chat_id, text, reply_markup=kb, parse_mode=parse_mode)
            await state.finish()
        elif pwd_check == 0:
            text = 'Неправильный номер договора или пароль. Попробуй еще раз!\n\nВведи номер договора.'
            await edit_inline_message(bot, chat_id, text, reply_markup=cancel_menu[1])
        else:
            text = 'Договор не найден.\nВведи номер другого договора.'
            await edit_inline_message(bot, chat_id, text, reply_markup=cancel_menu[1])
        data['pwd'] = ''
        await AgrmSettingsFSM.agrm.set()


@dp.callback_query_handler(text='settings-notify', state='*')
async def inline_cb_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(bot, query, 'Настройки уведомлений', 'notify')
    await state.finish()


@dp.callback_query_handler(text='settings-switch-notify')
@dp.callback_query_handler(text='settings-switch-mailing')
async def inline_cb_h_notify_settings(query: types.CallbackQuery):
    logger.info(f'Switching notify settings [{query.message.chat.id}]')
    if query.data == 'settings-switch-notify':
        await sql.switch_sub(query.message.chat.id, 'notify')
        await update_inline_query(bot, query, 'Обновления переключены', 'notify')
    else:
        await sql.switch_sub(query.message.chat.id, 'mailing')
        await update_inline_query(bot, query, 'Новости переключены', 'notify')


@dp.callback_query_handler(text='exit', state='*')
async def inline_cb_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(bot, query, 'Хотите выйти?', 'exit')
    await state.finish()


@dp.callback_query_handler(text='exit-yes')
async def inline_cb_h_notify_settings(query: types.CallbackQuery):
    logger.info(f'Exited [{query.message.chat.id}]')
    await query.answer('Успешный выход', show_alert=True)
    text = emojize('Ты успешно вышел. Возвращайся по-скорее! :smile:\nОтправь /start чтобы начать.')
    await edit_inline_message(bot, query.message.chat.id, text)
    await bot.unpin_all_chat_messages(query.message.chat.id)
    await sql.unsubscribe(query.message.chat.id)
    agrms = await sql.get_agrms(query.message.chat.id)
    for agrm in agrms:
        await sql.del_agrm(query.message.chat.id, agrm)


# @dp.message_handler(commands='test1')
# async def auth_cmd_handler(message: types.Message):
#     start = datetime.now()
#     logger.info(f'test1 at {start}')
#     await asyncio.sleep(10)
#     end = datetime.now() - start
#     logger.info(f'test1 ends in {end}')
#     await bot.send_message(message.chat.id, f'test1 in {end}')
#
#
# @dp.message_handler(commands='test2')
# async def auth_cmd_handler(message: types.Message):
#     start = datetime.now()
#     logger.info(f'test2 at {start}')
#     res = await get_account_pass('69420')
#     end = datetime.now() - start
#     logger.info(f'test2 ends in {end}')
#     await bot.delete_message(message.chat.id, message.message_id)
#     await bot.send_message(message.chat.id, f'test2 in {end}: {res}')
