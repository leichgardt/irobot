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
from src.lb import promise_payment
from src.payment.yoomoney import yoomoney_pay
from src.bot.api import main_menu, cancel_menu, clear_inline_message, get_keyboard_menu, update_inline_query, get_agrm_balances, edit_inline_message

from .l3_main import bot, dp


# @dp.callback_query_handler(text='payment')
# async def inline_cb_h_balance(query: types.CallbackQuery):
#     # agrms = await sql.get_agrms(query.message.chat.id)
#     # await update_inline_query(bot, query, 'Настройки договоров', 'payment', agrms)
#     await query.answer('платёж', show_alert=True)
#     await bot.send_invoice(query.message.chat.id, title='Оплата', description='Оплата договора', payload='05275',
#                            provider_token='381764678:TEST:25564', currency='RUB', start_parameter='test',
#                            prices=[{'label': 'Руб', 'amount': 7430}]
#                            )
#     # await clear_inline_message(bot, query.message.chat.id)
#     # res = await bot.send_message(query.message.chat.id, text, reply_markup=kb, parse_mode=types.ParseMode.HTML)
#     # await sql.upd_inline(query.message.chat.id, res.message_id, res.text)

class PaymentFSM(StatesGroup):
    oper = State()
    agrm = State()
    amount = State()


@dp.callback_query_handler(text='cancel', state=PaymentFSM.oper)
@dp.callback_query_handler(text='cancel', state=PaymentFSM.agrm)
@dp.callback_query_handler(text='cancel', state=PaymentFSM.amount)
@dp.callback_query_handler(text='payments', state='*')
async def inline_cb_h_payments(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await PaymentFSM.oper.set()
    await update_inline_query(bot, query, 'Платежи', 'payments')
    # await bot.send_chat_action(query.message.chat.id, 'typing')
    # await update_inline_query(bot, query, 'Список договоров', 'payments-agrm')
    # await PaymentFSM.agrm.set()


@dp.callback_query_handler(text='payments-promise', state=PaymentFSM.oper)
@dp.callback_query_handler(text='payments-online', state=PaymentFSM.oper)
async def inline_cb_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        logger.info(f'Start payment [{query.message.chat.id}]')
        await PaymentFSM.next()
        data['oper'] = 'promise' if query.data == 'payments-promise' else 'online'
        if data['oper'] == 'promise':
            await update_inline_query(bot, query, 'Список договоров', 'payments-promise-agrm')
        else:
            await update_inline_query(bot, query, 'Список договоров', 'payments-online-agrm')


@dp.callback_query_handler(Regexp(regexp=r'agrm-([^\s]*)'), state=PaymentFSM.agrm)
async def inline_cb_h_payments_agrm(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await PaymentFSM.next()
        data['agrm'] = query.data[5:]
        if data['oper'] == 'promise':
            _, kb, _ = await get_keyboard_menu('confirm')
            data['amount'] = 100
            text = 'Подключить обещанный платёж на 100 руб. на 5 дней?'
            await update_inline_query(bot, query, 'Обещанный платёж', text=text, keyboard=kb)
        else:
            text = 'На сколько хочешь пополнить счёт? Введи сумму.'
            await update_inline_query(bot, query, 'Обещанный платёж', text=text, keyboard=cancel_menu[1])


@dp.message_handler(lambda message: not message.text.isdigit(), state=PaymentFSM.amount)
async def inline_cb_h_payment(message: types.Message, state: FSMContext):
    text = 'Введи число.'
    await message.delete()
    await edit_inline_message(bot, message.chat.id, text=text, reply_markup=cancel_menu[1])


@dp.message_handler(lambda message: message.text.isdigit(), state=PaymentFSM.amount)
async def inline_cb_h_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = message.text
        text = 'Оплата онлайн\n\nДоговор: {agrm}\nК оплате: {sum}\nПоступит на счёт: {tax}'
        url = await yoomoney_pay(data['agrm'], data['amount'])
        kb = types.InlineKeyboardMarkup()
        btn = [types.InlineKeyboardButton(text='Оплатить', url=url),
               types.InlineKeyboardButton(text='Отмена', callback_data='main-menu')]
        kb.add(*btn)
        await message.delete()
        await edit_inline_message(bot, message.chat.id, text, reply_markup=kb)


@dp.callback_query_handler(text='no', state=PaymentFSM.amount)
async def inline_cb_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(bot, query, 'Главное меню', text=main_menu[0], keyboard=main_menu[1], parse_mode=main_menu[2])
    await state.finish()


@dp.callback_query_handler(text='yes', state=PaymentFSM.amount)
async def inline_cb_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        agrm_id = await sql.get_agrm_id(query.message.chat.id, data['agrm'])
        res = await promise_payment(agrm_id, data['amount'])
        if res:
            logger.info(f'Payment success [{query.message.chat.id}]')
            text = 'Обещанный платёж успешно подключен! :tada:'
            await update_inline_query(bot, query, 'Успех!', text=emojize(text), keyboard=main_menu[1], parse_mode=main_menu[2])
        else:
            logger.info(f'Payment failure [{query.message.chat.id}]')
            text = 'Не удалось подключить обещанный платёж.'
            await update_inline_query(bot, query, 'Неудача!', text=text, keyboard=main_menu[1], parse_mode=main_menu[2])
        await state.finish()


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
