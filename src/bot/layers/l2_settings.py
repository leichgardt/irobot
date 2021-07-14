from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, edit_inline_message, get_keyboard, update_inline_query, delete_message, \
    private_and_login_require, get_hash, get_login_url
from src.bot import keyboards
from src.bot.text import Texts
from .l1_auth import bot, dp


class AgrmSettingsFSM(StatesGroup):
    agrms = State()
    agrm = State()


@dp.message_handler(commands='settings', state='*')
@dp.message_handler(Text('🔧 Настройки', ignore_case=True), state='*')
@private_and_login_require(do_not_check_sub=True)
async def message_h_settings(message: types.Message, state: FSMContext):
    await state.finish()
    if await sql.get_sub(message.chat.id):
        kb = get_keyboard(keyboards.settings_menu_btn, keyboard_type='inline')
        _, text, parse = Texts.settings.full()
        await AgrmSettingsFSM.agrm.set()
        await state.update_data(agrms=await sql.get_agrms(message.chat.id))
    else:
        kb = None
        _, text, parse = Texts.settings_non_auth.full()
    res = await bot.send_message(message.chat.id, text, parse_mode=parse, reply_markup=kb)
    await sql.upd_inline(message.chat.id, res.message_id, text, parse)


@dp.callback_query_handler(text='settings', state=AgrmSettingsFSM.agrm)
async def inline_h_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.settings.full(), btn_list=[keyboards.settings_menu_btn])


@dp.callback_query_handler(text='settings-done', state=AgrmSettingsFSM.agrm)
async def inline_h_settings_done(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await query.answer(Texts.settings_done.answer, show_alert=True)
    await delete_message(query.message)
    await bot.send_message(query.message.chat.id, Texts.main_menu, parse_mode=Texts.main_menu.parse_mode, reply_markup=main_menu)
    await sql.upd_inline(query.message.chat.id, 0, '')


@dp.callback_query_handler(text='cancel', state=[AgrmSettingsFSM.agrms, AgrmSettingsFSM.agrm])
@dp.callback_query_handler(text='settings-my-agrms', state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_settings(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if 'agrms' not in data.keys():
            data['agrms'] = await sql.get_agrms(query.message.chat.id)
        btn_list = [await keyboards.get_agrms_btn(agrms=data['agrms']), keyboards.agrms_settings_btn]
        await update_inline_query(query, *Texts.settings_agrms.full(), btn_list=btn_list)


@dp.callback_query_handler(Regexp(regexp=r'agrm-(?!del)(?!del-yes)(?!del-no)(?!add)([^\s]*)'), state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_control(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['agrm'] = query.data[5:]
        await update_inline_query(query, Texts.settings_agrm.answer.format(agrm=data['agrm']),
                                  Texts.settings_agrm.format(agrm=data['agrm']), Texts.settings_agrm.parse_mode,
                                  btn_list=[keyboards.agrm_control_btn])


@dp.callback_query_handler(text='agrm-del', state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_del(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sql.deactivate_agrm(query.message.chat.id, data['agrm'])
        data['agrms'] = await sql.get_agrms(query.message.chat.id)
        btn_list = [await keyboards.get_agrms_btn(query.message.chat.id), keyboards.agrms_settings_btn]
        await update_inline_query(query, Texts.settings_agrm_del_answer.format(agrm=data['agrm']),
                                  Texts.settings_agrms, Texts.settings_agrms.parse_mode, btn_list=btn_list)
        await alogger.info(f'Agrm {data["agrm"]} deactivated [{query.message.chat.id}]')


@dp.callback_query_handler(text='agrm-add', state=AgrmSettingsFSM.agrm)
async def inline_h_agrm_del(query: types.CallbackQuery, state: FSMContext):
    hash_code = get_hash(query.message.chat.id)
    url = get_login_url(hash_code)
    await update_inline_query(query, *Texts.settings_agrm_add.full(), btn_list=[keyboards.get_login_btn(url)])
    await sql.upd_hash(query.message.chat.id, hash_code)
    await alogger.info(f'Agrm adding [{query.message.chat.id}]')


@dp.callback_query_handler(text='settings-notify', state=AgrmSettingsFSM.agrm)
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id), keyboards.back_to_settings]
    await update_inline_query(query, *Texts.settings_notify.full(), reply_markup=get_keyboard(btn_list, lining=False))


@dp.callback_query_handler(text='settings-switch-notify', state=AgrmSettingsFSM.agrm)
@dp.callback_query_handler(text='settings-switch-mailing', state=AgrmSettingsFSM.agrm)
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    if query.data == 'settings-switch-notify':
        await sql.switch_sub(query.message.chat.id, 'notify')
        answer = Texts.settings_notify_switch_answer
    else:
        await sql.switch_sub(query.message.chat.id, 'mailing')
        answer = Texts.settings_mailing_switch_answer
    btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id), keyboards.back_to_settings]
    await update_inline_query(query, answer, Texts.settings_notify, Texts.settings_notify.parse_mode,
                              reply_markup=get_keyboard(btn_list, lining=False))
    await alogger.info(f'Switching notify settings [{query.message.chat.id}]')


@dp.callback_query_handler(text='exit', state=AgrmSettingsFSM.agrm)
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.settings_exit.full(), btn_list=[keyboards.exit_confirm_btn])


@dp.callback_query_handler(text='exit-yes', state=AgrmSettingsFSM.agrm)
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await query.answer(Texts.settings_exited.answer, show_alert=True)
        await edit_inline_message(query.message.chat.id, Texts.settings_exited, reply_markup=types.ReplyKeyboardRemove())
        await alogger.info(f'Exiting [{query.message.chat.id}]')
        await sql.unsubscribe(query.message.chat.id)
        for agrm in data['agrms']:
            await sql.deactivate_agrm(query.message.chat.id, agrm)
        await state.finish()
