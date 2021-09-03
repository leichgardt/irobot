from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.bot.api import (main_menu, get_keyboard, update_inline_query, delete_message, private_and_login_require,
                         get_hash, get_login_url, run_cmd)
from src.bot import keyboards
from src.bot.api import get_all_agrm_data
from src.text import Texts
from src.sql import sql
from src.utils import alogger

from .l1_auth import bot, dp


class AccountSettingsFSM(StatesGroup):
    accounts = State()
    mailing = State()
    acc = State()


@dp.message_handler(commands='settings', state='*')
@dp.message_handler(Text('🔧 Настройки', ignore_case=True), state='*')
@private_and_login_require(do_not_check_sub=True)
async def message_h_settings(message: types.Message, state: FSMContext):
    await run_cmd(bot.send_chat_action(message.chat.id, 'typing'))
    await state.finish()
    data = await sql.get_sub(message.chat.id)
    if data:
        kb = get_keyboard(keyboards.settings_menu_btn)
        _, text, parse = Texts.settings.full()
        await AccountSettingsFSM.acc.set()
        await state.update_data(mailing=data[0])
    else:
        kb = None
        _, text, parse = Texts.settings_non_auth.full()
    res = await run_cmd(bot.send_message(message.chat.id, text, parse_mode=parse, reply_markup=kb))
    await sql.upd_inline(message.chat.id, res.message_id, text, parse)


@dp.callback_query_handler(text='settings', state=AccountSettingsFSM.acc)
async def inline_h_settings(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.settings.full(), btn_list=[keyboards.settings_menu_btn])


@dp.callback_query_handler(text='settings-done', state=AccountSettingsFSM.acc)
async def inline_h_settings_done(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await query.answer(Texts.settings_done.answer, show_alert=True)
    await delete_message(query.message)
    await run_cmd(bot.send_message(query.message.chat.id, Texts.main_menu, parse_mode=Texts.main_menu.parse_mode,
                                   reply_markup=main_menu))
    await sql.upd_inline(query.message.chat.id, 0, '')


@dp.callback_query_handler(text='cancel', state=[AccountSettingsFSM.accounts, AccountSettingsFSM.acc])
@dp.callback_query_handler(text='settings-my-accounts', state=AccountSettingsFSM.acc)
async def inline_h_account_settings(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['accounts'] = await get_all_agrm_data(query.message.chat.id, only_numbers=True)
        ans, txt, prs = Texts.settings_accounts.full()
        txt = txt.format(accounts=Texts.get_account_agrm_list(data['accounts']))
        btn_list = [await keyboards.get_agrms_btn(custom=data['accounts'], prefix='account'), keyboards.account_settings_btn]
        await update_inline_query(query, ans, txt, prs, btn_list=btn_list)


@dp.callback_query_handler(Regexp(regexp=r'account-([^\s]*)'), state=AccountSettingsFSM.acc)
async def inline_h_account_control(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['acc'] = query.data.replace('account-', '')
        await update_inline_query(query, Texts.settings_account.answer.format(account=data['acc']),
                                  Texts.settings_account.format(account=data['acc']), Texts.settings_account.parse_mode,
                                  btn_list=[keyboards.account_control_btn])


@dp.callback_query_handler(text='del-account', state=AccountSettingsFSM.acc)
async def inline_h_account_del(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sql.deactivate_account(query.message.chat.id, data['acc'])
        data['accounts'] = await get_all_agrm_data(query.message.chat.id, only_numbers=True)
        await update_inline_query(
            query,
            Texts.settings_account_del_answer.format(account=data['acc']),
            Texts.settings_accounts.format(accounts=Texts.get_account_agrm_list(data['accounts'])),
            Texts.settings_accounts.parse_mode,
            btn_list=[await keyboards.get_agrms_btn(custom=data['accounts']), keyboards.account_settings_btn]
        )
        await alogger.info(f'Account {data["acc"]} deactivated [{query.message.chat.id}]')


@dp.callback_query_handler(text='add-account', state=AccountSettingsFSM.acc)
async def inline_h_account_del(query: types.CallbackQuery, state: FSMContext):
    await AccountSettingsFSM.acc.set()
    hash_code = get_hash(query.message.chat.id)
    url = get_login_url(hash_code)
    kb = get_keyboard(keyboards.get_login_btn(url), keyboards.cancel_btn, lining=False)
    await update_inline_query(query, *Texts.settings_account_add.full(), reply_markup=kb)
    await sql.upd_hash(query.message.chat.id, hash_code)
    await alogger.info(f'Account adding [{query.message.chat.id}]')


@dp.callback_query_handler(text='settings-notify', state=AccountSettingsFSM.acc)
async def inline_h_notify_settings(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id), keyboards.back_to_settings]
        texts = Texts.settings_notify.full() if data['mailing'] else Texts.settings_notify_enable.full()
        await update_inline_query(query, *texts, reply_markup=get_keyboard(btn_list, lining=False))


@dp.callback_query_handler(text='settings-switch-notify', state=AccountSettingsFSM.acc)
@dp.callback_query_handler(text='settings-switch-mailing', state=AccountSettingsFSM.acc)
async def inline_h_switch_notify(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await sql.switch_sub(query.message.chat.id, 'mailing')
        btn_list = [await keyboards.get_notify_settings_btn(query.message.chat.id), keyboards.back_to_settings]
        data['mailing'] = not data['mailing']
        _, text, parse = Texts.settings_notify.full() if data['mailing'] else Texts.settings_notify_enable.full()
        answer = Texts.settings_mailing_switch_answer
        await update_inline_query(query, answer, text, parse, reply_markup=get_keyboard(btn_list, lining=False))
        await alogger.info(f'Switching notify settings [{query.message.chat.id}]')


@dp.callback_query_handler(text='exit', state=AccountSettingsFSM.acc)
async def inline_h_exit(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.settings_exit.full(), btn_list=[keyboards.exit_confirm_btn])


@dp.callback_query_handler(text='exit-yes', state=AccountSettingsFSM.acc)
async def inline_h_exit_confirm(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await query.answer(Texts.settings_exited.answer, show_alert=True)
        await run_cmd(query.message.delete())
        await run_cmd(bot.send_message(query.message.chat.id, Texts.settings_exited, reply_markup=types.ReplyKeyboardRemove()))
        await alogger.info(f'Exiting [{query.message.chat.id}]')
        await sql.unsubscribe(query.message.chat.id)
        for acc in await get_all_agrm_data(query.message.chat.id, only_numbers=True):
            await sql.deactivate_account(query.message.chat.id, acc)
        await state.finish()
