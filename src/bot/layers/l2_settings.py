from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.utils import alogger
from src.sql import sql
from src.lb import check_account_pass
from src.bot.api import main_menu, edit_inline_message, cancel_menu, get_keyboard, keyboards, update_inline_query, delete_message
from src.bot.text import Texts
from .l1_auth import bot, dp


@dp.message_handler(commands='settings', state='*')
@dp.message_handler(Text('🔧 Настройки', ignore_case=True), state='*')
async def message_h_settings(message: types.Message, state: FSMContext):
    await state.finish()
    if await sql.get_sub(message.chat.id):
        kb = get_keyboard(keyboards.settings_menu_btn, keyboard_type='inline')
        _, text, parse = Texts.settings.full()
    else:
        kb = None
        _, text, parse = Texts.settings_non_auth.full()
    res = await bot.send_message(message.chat.id, text, parse_mode=parse, reply_markup=kb)
    await sql.upd_inline(message.chat.id, res.message_id, text, parse)


@dp.callback_query_handler(text='settings', state='*')
async def inline_h_settings(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(bot, query, Texts.settings.answer, Texts.settings, parse_mode=Texts.settings.parse_mode,
                              btn_list=[keyboards.settings_menu_btn])
    await AgrmSettingsFSM.agrm.set()


@dp.callback_query_handler(text='settings-done', state='*')
async def inline_h_settings_done(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await query.answer(Texts.settings_done.answer, show_alert=True)
    await query.message.edit_text(Texts.settings_done, parse_mode=Texts.settings_done.parse_mode)
    await bot.send_message(query.message.chat.id, Texts.main_menu, parse_mode=Texts.main_menu.parse_mode, reply_markup=main_menu)
    await sql.upd_inline(query.message.chat.id, 0, '')


class AgrmSettingsFSM(StatesGroup):
    agrm = State()
    pwd = State()


@dp.callback_query_handler(text='cancel', state=[AgrmSettingsFSM.agrm, AgrmSettingsFSM.pwd])
@dp.callback_query_handler(text='settings-my-agrms', state='*')
async def inline_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await AgrmSettingsFSM.agrm.set()
    btn_list = [await keyboards.get_agrms_btn(query.message.chat.id), keyboards.agrms_settings_btn]
    await update_inline_query(bot, query, *Texts.settings_agrms.full(), btn_list=btn_list)


@dp.callback_query_handler(Regexp(regexp=r'agrm-(?!del)(?!del-yes)(?!del-no)(?!add)([^\s]*)'),
                           state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_control(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['agrm'] = query.data[5:]
        await update_inline_query(bot, query, Texts.settings_agrm.answer.format(agrm=data['agrm']),
                                  Texts.settings_agrm.format(agrm=data['agrm']), Texts.settings_agrm.parse_mode,
                                  btn_list=[keyboards.agrm_control_btn])


@dp.callback_query_handler(text='agrm-del', state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_del(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await state.finish()
        await AgrmSettingsFSM.agrm.set()
        await sql.del_agrm(query.message.chat.id, data['agrm'])
        btn_list = [await keyboards.get_agrms_btn(query.message.chat.id), keyboards.agrms_settings_btn]
        await update_inline_query(bot, query, Texts.settings_agrm_del_answer.format(agrm=data['agrm']),
                                  Texts.settings_agrms, Texts.settings_agrms.parse_mode, btn_list=btn_list)
        await alogger.info(f'Agrm {data["agrm"]} deleted [{query.message.chat.id}]')


@dp.callback_query_handler(text='agrm-add', state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_del(query: types.CallbackQuery, state: FSMContext):
    await state.update_data(agrm='')
    await update_inline_query(bot, query, *Texts.settings_agrm_add.full(), keyboard=cancel_menu['inline'])
    await alogger.info(f'Agrm adding [{query.message.chat.id}]')


@dp.message_handler(state=AgrmSettingsFSM.agrm)
async def fsm_auth_agrm_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['agrm'] = message.text
        await delete_message(message)
        if data['agrm'] in await sql.get_agrms(message.chat.id):
            await edit_inline_message(bot, message.chat.id, Texts.settings_agrm_exist.format(agrm=data['agrm']),
                                      Texts.settings_agrm_exist.parse_mode, reply_markup=cancel_menu['inline'])
        else:
            await AgrmSettingsFSM.next()
            await edit_inline_message(bot, message.chat.id, Texts.settings_agrm_pwd.format(agrm=data['agrm']),
                                      Texts.settings_agrm_pwd.parse_mode, reply_markup=cancel_menu['inline'])


@dp.message_handler(state=AgrmSettingsFSM.pwd)
async def fsm_auth_pwd_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await delete_message(message)
        pwd_check, agrm_id = await check_account_pass(data['agrm'], message.text)
        if pwd_check == 1:
            await sql.add_agrm(message.chat.id, data['agrm'], agrm_id)
            await state.finish()
            kb = get_keyboard(await keyboards.get_agrms_btn(message.chat.id), keyboards.agrms_settings_btn)
            await edit_inline_message(bot, message.chat.id, Texts.settings_agrm_add_success.format(agrm=data['agrm']),
                                      Texts.settings_agrm_add_success.parse_mode, reply_markup=kb)
            await alogger.info(f'Agrm {data["agrm"]} added [{message.chat.id}]')
        elif pwd_check == 0:
            await edit_inline_message(bot, message.chat.id, Texts.settings_agrm_add_fail,
                                      Texts.settings_agrm_add_fail.parse_mode, reply_markup=cancel_menu['inline'])
        else:
            await edit_inline_message(bot, message.chat.id, Texts.settings_agrm_add_error,
                                      Texts.settings_agrm_add_error.parse_mode, reply_markup=cancel_menu['inline'])
        await AgrmSettingsFSM.agrm.set()


@dp.callback_query_handler(text='settings-notify', state='*')
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id), keyboards.back_to_settings]
    await update_inline_query(bot, query, *Texts.settings_notify.full(), btn_list=btn_list)


@dp.callback_query_handler(text='settings-switch-notify')
@dp.callback_query_handler(text='settings-switch-mailing')
async def inline_h_notify_settings(query: types.CallbackQuery):
    if query.data == 'settings-switch-notify':
        await sql.switch_sub(query.message.chat.id, 'notify')
        answer = Texts.settings_notify_switch_answer
    else:
        await sql.switch_sub(query.message.chat.id, 'mailing')
        answer = Texts.settings_mailing_switch_answer
    btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id), keyboards.back_to_settings]
    await update_inline_query(bot, query, answer, Texts.settings_notify,
                              Texts.settings_notify.parse_mode, btn_list=btn_list)
    await alogger.info(f'Switching notify settings [{query.message.chat.id}]')


@dp.callback_query_handler(text='exit', state='*')
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(bot, query, *Texts.settings_exit.full())


@dp.callback_query_handler(text='exit-yes')
async def inline_h_notify_settings(query: types.CallbackQuery):
    await sql.unsubscribe(query.message.chat.id)
    await query.answer(Texts.settings_exited.answer, show_alert=True)
    await edit_inline_message(bot, query.message.chat.id, Texts.settings_exited)
    agrms = await sql.get_agrms(query.message.chat.id)
    for agrm in agrms:
        await sql.del_agrm(query.message.chat.id, agrm)
    await alogger.info(f'Exited [{query.message.chat.id}]')
