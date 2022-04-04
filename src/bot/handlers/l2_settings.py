from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.bot import keyboards
from src.bot.api import (
    update_inline_query,
    private_and_login_require,
    get_login_url,
    exc_handler,
    get_all_agrm_data,
    Keyboard
)
from src.sql import sql
from src.text import Texts
from src.utils import logger, get_hash
from .l1_auth import bot, dp


class AccountSettingsFSM(StatesGroup):
    accounts = State()
    mailing = State()
    acc = State()


@dp.message_handler(commands='settings', state='*')
@dp.message_handler(Text('🔧 Настройки', ignore_case=True), state='*')
@private_and_login_require(do_not_check_sub=True)
@exc_handler
async def message_h_settings(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, 'typing')
    await state.finish()
    data = await sql.get_sub(message.chat.id)
    if data:
        kb = keyboards.settings_menu_kb
        text, parse_mode = Texts.settings.pair()
        await AccountSettingsFSM.acc.set()
        await state.update_data(mailing=data[0])
    else:
        kb = None
        text, parse_mode = Texts.settings_non_auth.pair()
    res = await bot.send_message(message.chat.id, text, parse_mode=parse_mode, reply_markup=kb)
    await sql.upd_inline_message(message.chat.id, res.message_id, text, parse_mode)


@dp.callback_query_handler(text='settings', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.settings.full(), reply_markup=keyboards.settings_menu_kb)


@dp.callback_query_handler(text='settings-done', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_settings_done(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(query, *Texts.settings_done.full(), alert=True, skip_db_update=True)
    await bot.send_message(query.message.chat.id, *Texts.main_menu.pair(), reply_markup=keyboards.main_menu_kb)
    await sql.upd_inline_message(query.message.chat.id, 0, '')


@dp.callback_query_handler(text='cancel', state=[AccountSettingsFSM.accounts, AccountSettingsFSM.acc])
@dp.callback_query_handler(text='settings-my-accounts', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_account_settings(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['accounts'] = await get_all_agrm_data(query.message.chat.id, only_numbers=True)
        ans, txt, prs = Texts.settings_accounts.full(accounts=Texts.get_account_agrm_list(data['accounts']))
        btn_list = await keyboards.get_agrms_btn(custom=data['accounts'], prefix='account')
        await update_inline_query(query, ans, txt, prs, btn_list=btn_list + [keyboards.account_settings_btn])


@dp.callback_query_handler(Regexp(regexp=r'account-([^\s]*)'), state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_account_control(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['acc'] = query.data.replace('account-', '')
        await update_inline_query(query, *Texts.settings_account.full(account=data['acc']),
                                  btn_list=[keyboards.account_control_btn])


@dp.callback_query_handler(text='del-account', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_account_del(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sql.deactivate_account(query.message.chat.id, data['acc'])
        data['accounts'] = await get_all_agrm_data(query.message.chat.id, only_numbers=True)
        await update_inline_query(
            query,
            Texts.settings_account_del_answer.format(account=data['acc']),
            Texts.settings_accounts.format(accounts=Texts.get_account_agrm_list(data['accounts'])),
            Texts.settings_accounts.parse_mode,
            btn_list=await keyboards.get_agrms_btn(custom=data['accounts']) + [keyboards.account_settings_btn]
        )
        await logger.info(f'Account {data["acc"]} deactivated [{query.message.chat.id}]')


@dp.callback_query_handler(text='add-account', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_account_del(query: types.CallbackQuery, state: FSMContext):
    await AccountSettingsFSM.acc.set()
    hash_code = get_hash(query.message.chat.id)
    url = get_login_url(hash_code)
    kb = Keyboard(keyboards.get_login_btn(url) + keyboards.cancel_btn).inline()
    await update_inline_query(query, *Texts.settings_account_add.full(), reply_markup=kb)
    await sql.upd_hash(query.message.chat.id, hash_code)
    await logger.info(f'Account adding [{query.message.chat.id}]')


@dp.callback_query_handler(text='settings-notify', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        texts = Texts.settings_notify.full() if data['mailing'] else Texts.settings_notify_enable.full()
        btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id)]
        await update_inline_query(query, *texts, reply_markup=Keyboard(btn_list).inline())


@dp.callback_query_handler(text='settings-switch-notify', state=AccountSettingsFSM.acc)
@dp.callback_query_handler(text='settings-switch-mailing', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_switch_notify(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sql.switch_sub(query.message.chat.id, 'mailing')
        data['mailing'] = not data['mailing']
        text, parse_mode = Texts.settings_notify.pair() if data['mailing'] else Texts.settings_notify_enable.pair()
        btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id)]
        await update_inline_query(query, Texts.settings_mailing_switch_answer, text, parse_mode,
                                  reply_markup=Keyboard(btn_list).inline())
        await logger.info(f'Switching notify settings [{query.message.chat.id}]')


@dp.callback_query_handler(text='exit', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_exit(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.settings_exit.full(), btn_list=[keyboards.exit_confirm_btn])


@dp.callback_query_handler(text='exit-yes', state=AccountSettingsFSM.acc)
@exc_handler
async def inline_h_exit_confirm(query: types.CallbackQuery, state: FSMContext):
    await query.answer(Texts.settings_exited.answer, show_alert=True)
    await query.message.delete()
    await bot.send_message(query.message.chat.id, Texts.settings_exited, reply_markup=types.ReplyKeyboardRemove())
    await logger.info(f'Exiting [{query.message.chat.id}]')
    await sql.unsubscribe(query.message.chat.id)
    for acc in await get_all_agrm_data(query.message.chat.id, only_numbers=True):
        await sql.deactivate_account(query.message.chat.id, acc)
    await state.finish()
