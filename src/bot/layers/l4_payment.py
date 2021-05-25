import hashlib
import asyncio

from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, StateFilter, RegexpCommandsFilter, Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.utils import alogger
from src.sql import sql
from src.lb import promise_payment
from src.payment.yoomoney import yoomoney_pay
from src.bot.api import main_menu, cancel_menu, edit_inline_message, update_inline_query, get_keyboard, keyboards, \
    delete_message, private_and_login_require
from src.bot.text import Texts

from .l3_main import bot, dp


class PaymentFSM(StatesGroup):
    oper = State()
    agrm = State()
    amount = State()


@dp.message_handler(Text(emojize(':moneybag: Платежи')), state='*')
@private_and_login_require()
async def message_h_payments(message: types.Message, state: FSMContext):
    await state.finish()
    await PaymentFSM.oper.set()
    kb = get_keyboard(keyboards.payment_choice_btn, keyboard_type='inline')
    res = await bot.send_message(message.chat.id, Texts.payments, Texts.payments.parse_mode, reply_markup=kb)
    await sql.upd_inline(message.chat.id, res.message_id, res.text, Texts.payments.parse_mode)


@dp.callback_query_handler(text='payments-promise', state=PaymentFSM.oper)
@dp.callback_query_handler(text='payments-online', state=PaymentFSM.oper)
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await PaymentFSM.next()
        data['oper'] = 'promise' if query.data == 'payments-promise' else 'online'
        agrms = await sql.get_agrms(query.message.chat.id)
        if len(agrms) == 0:
            answer, text, parse = Texts.balance_no_agrms.full()
            kb = main_menu
            await state.finish()
        elif len(agrms) == 1:
            data['agrm'] = agrms[0]
            if data['oper'] == 'promise':
                agrms = await keyboards.get_promise_payment_agrms(query.message.chat.id, agrms)
                if agrms:
                    data['amount'] = 100
                    answer, text, parse = Texts.payments_promise_offer.full()
                    kb = get_keyboard(keyboards.confirm_btn)
                    await PaymentFSM.amount.set()
                else:
                    answer, text, parse = Texts.payments_already_have.full()
                    kb = main_menu
                    await state.finish()
            else:
                answer, text, parse = Texts.payments_online_amount.full()
                kb = cancel_menu['inline']
                await PaymentFSM.amount.set()
            answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        else:
            if data['oper'] == 'promise':
                answer, text, parse = Texts.payments_promise.full()
                kb = get_keyboard(await keyboards.get_promise_payment_btn(query.message.chat.id, agrms), keyboards.back_to_main)
            else:
                answer, text, parse = Texts.payments_online.full()
                kb = get_keyboard(await keyboards.get_agrms_btn(agrms=agrms), keyboards.back_to_main)
        await update_inline_query(bot, query, answer, text, parse, keyboard=kb)
        await alogger.info(f'Start payment [{query.message.chat.id}]')


@dp.callback_query_handler(Regexp(regexp=r'agrm-([^\s]*)'), state=PaymentFSM.agrm)
async def inline_h_payments_agrm(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await PaymentFSM.next()
        data['agrm'] = query.data[5:]
        if data['oper'] == 'promise':
            data['amount'] = 100
            answer, text, parse = Texts.payments_promise_offer.full()
            kb = get_keyboard(keyboards.confirm_btn)
        else:
            answer, text, parse = Texts.payments_online_amount.full()
            kb = cancel_menu['inline']
        answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        await update_inline_query(bot, query, answer, text, parse, keyboard=kb)


@dp.message_handler(lambda message: not message.text.isdigit(), state=PaymentFSM.amount)
async def inline_h_payment(message: types.Message, state: FSMContext):
    await edit_inline_message(bot, message.chat.id, Texts.payments_online_amount_is_not_digit,
                              Texts.payments_online_amount_is_not_digit.parse_mode, cancel_menu['inline'])
    await delete_message(message)


@dp.message_handler(lambda message: message.text.isdigit(), state=PaymentFSM.amount)
async def inline_h_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await bot.send_chat_action(message.chat.id, 'typing')
        data['amount'] = message.text
        text = Texts.payments_online_offer.format(agrm=data['agrm'], amount=float(data['amount']),
                                                  tax=float(data['amount']) * 0.05, res=float(data['amount']) * 0.95)
        url = await yoomoney_pay(data['agrm'], data['amount'])
        kb = get_keyboard(keyboards.get_payment_url_btn(url))
        await edit_inline_message(bot, message.chat.id, text, Texts.payments_online_offer.parse_mode, kb)
        await delete_message(message)


@dp.callback_query_handler(text='no', state=PaymentFSM.amount)
async def inline_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(bot, query, Texts.cancel.answer, Texts.cancel, Texts.cancel.parse_mode)
    await bot.send_message(query.message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode, reply_markup=main_menu)


@dp.callback_query_handler(text='yes', state=PaymentFSM.amount)
@dp.async_task
async def inline_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        agrm_id = await sql.get_agrm_id(query.message.chat.id, data['agrm'])
        res = await promise_payment(agrm_id, data['amount'])
        if res:
            answer, text, parse = Texts.payments_promise_success.full()
            await alogger.info(f'Payment success [{query.message.chat.id}]')
        else:
            answer, text, parse = Texts.payments_promise_fail.full()
            await alogger.warning(f'Payment failure [{query.message.chat.id}]')
        await update_inline_query(bot, query, answer, text, parse, alert=True)
        await state.finish()
        await bot.send_message(query.message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode, reply_markup=main_menu)


@dp.callback_query_handler(text='cancel', state=[PaymentFSM.oper, PaymentFSM.agrm, PaymentFSM.amount])
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await update_inline_query(bot, query, *Texts.cancel.full())
    await bot.send_message(query.message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode, reply_markup=main_menu)


# @dp.inline_handler()
# async def inline_payment_h(inline_query: types.InlineQuery):
#     """
#     Inline handler
#
#     Обработка встроенных запросов
#     Выдача ссылок на оплату
#     """
#     if await sql.get_sub(inline_query.from_user.id):
#         data = inline_query.query
#         agrms = await sql.get_agrms(inline_query.from_user.id)
#         items = []
#         for agrm in agrms:
#             if data in agrm:
#                 text = f'Договор {agrm}. Баланс: ##'
#                 content = f'Ссылка на пополнение баланса:\nhttps://ironnet.info/payment?agrm={agrm}'
#                 input_content = types.InputTextMessageContent(content)
#                 result_id: str = hashlib.md5(text.encode()).hexdigest()
#                 item = types.InlineQueryResultArticle(
#                     id=result_id,
#                     title=text,
#                     input_message_content=input_content,
#                 )
#                 items.append(item)
#         await bot.answer_inline_query(inline_query.id, results=items, cache_time=1)
#     else:
#         text = f'Вы не вошли в учётную запись.'
#         content = 'Вы не вошли в учётную запись. Чтобы авторизоваться, отправьте команду /start мне в ЛС.'
#         input_content = types.InputTextMessageContent(content)
#         result_id: str = hashlib.md5(text.encode()).hexdigest()
#         item = types.InlineQueryResultArticle(
#             id=result_id,
#             title=text,
#             input_message_content=input_content,
#         )
#         await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)
