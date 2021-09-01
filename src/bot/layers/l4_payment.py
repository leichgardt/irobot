import ujson

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.bot import keyboards
from src.bot.api import (main_menu, cancel_menu, edit_inline_message, update_inline_query, get_keyboard, delete_message,
                         private_and_login_require, get_payment_hash, run_cmd, get_invoice_params, get_payment_tax)
from src.bot.text import Texts
from src.lb import promise_payment, get_balance, payment
from src.sql import sql
from src.utils import alogger, map_format

from .l3_main import bot, dp


class PaymentFSM(StatesGroup):
    operation = State()
    agrm = State()
    balance = State()
    amount = State()
    payment = State()
    hash = State()


@dp.message_handler(Text(emojize(':moneybag: Платежи')), state='*')
@private_and_login_require()
async def message_h_payments(message: types.Message, state: FSMContext):
    await state.finish()
    await PaymentFSM.operation.set()
    kb = get_keyboard(keyboards.payment_choice_btn, keyboard_type='inline')
    res = await run_cmd(bot.send_message(message.chat.id, Texts.payments, Texts.payments.parse_mode, reply_markup=kb))
    await sql.upd_inline(message.chat.id, res.message_id, res.text, Texts.payments.parse_mode)


@dp.callback_query_handler(text='payments-online', state=PaymentFSM.operation)
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    """ Оплата онлайн """
    async with state.proxy() as data:
        await PaymentFSM.next()
        data['operation'] = 'online'
        agrms = await sql.get_agrms(query.message.chat.id)
        if len(agrms) == 0:
            answer, text, parse = Texts.balance_no_agrms.full()
            kb = main_menu
            await state.finish()
        elif len(agrms) == 1:
            data['agrm'] = agrms[0]
            answer, text, parse = Texts.payments_online_amount.full()
            balance = await get_balance(data['agrm'])
            data['balance'] = balance['balance']
            text = map_format(text, balance=data['balance'])
            kb = cancel_menu['inline']
            await PaymentFSM.amount.set()
            answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        else:
            answer, text, parse = Texts.payments_online.full()
            kb = get_keyboard(await keyboards.get_agrms_btn(custom=agrms), keyboards.back_to_main)
        await update_inline_query(query, answer, text, parse, reply_markup=kb)


@dp.callback_query_handler(text='payments-promise', state=PaymentFSM.operation)
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    """ Обещанный платёж """
    async with state.proxy() as data:
        await PaymentFSM.next()
        data['operation'] = 'promise'
        agrms = await sql.get_agrms(query.message.chat.id)
        if len(agrms) == 0:
            answer, text, parse = Texts.balance_no_agrms.full()
            kb = main_menu
            await state.finish()
        elif len(agrms) == 1:
            data['agrm'] = agrms[0]
            agrms = await keyboards.get_promise_payment_agrms(query.message.chat.id, agrms)
            if agrms:
                data['amount'] = 100
                answer, text, parse = Texts.payments_promise_offer.full()
                kb = get_keyboard(keyboards.confirm_btn)
                await PaymentFSM.amount.set()
            else:
                answer, text, parse = Texts.payments_promise_already_have.full()
                kb = main_menu
                await state.finish()
            answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        else:
            answer, text, parse = Texts.payments_promise.full()
            kb = get_keyboard(await keyboards.get_promise_payment_btn(query.message.chat.id, agrms),
                              keyboards.back_to_main)
        await update_inline_query(query, answer, text, parse, reply_markup=kb)


@dp.callback_query_handler(Regexp(regexp=r'agrm-([^\s]*)'), state=PaymentFSM.agrm)
async def inline_h_payments_agrm(query: types.CallbackQuery, state: FSMContext):
    """ Выбор договора для платежа """
    async with state.proxy() as data:
        await PaymentFSM.amount.set()
        data['agrm'] = query.data[5:]
        if data['operation'] == 'promise':
            data['amount'] = 100
            answer, text, parse = Texts.payments_promise_offer.full()
            kb = get_keyboard(keyboards.confirm_btn)
        else:
            answer, text, parse = Texts.payments_online_amount.full()
            balance = await get_balance(data['agrm'])
            data['balance'] = balance['balance']
            text = map_format(text, balance=data['balance'])
            kb = cancel_menu['inline']
        answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        await update_inline_query(query, answer, text, parse, reply_markup=kb)


@dp.message_handler(lambda message: not message.text.isdigit(), state=PaymentFSM.amount)
async def inline_h_payment(message: types.Message, state: FSMContext):
    """ Если текст сообщения - не число """
    await edit_inline_message(message.chat.id, Texts.payments_online_amount_is_not_digit,
                              Texts.payments_online_amount_is_not_digit.parse_mode, cancel_menu['inline'])
    await delete_message(message)


@dp.message_handler(lambda message: message.text.isdigit(), state=PaymentFSM.amount)
async def inline_h_payment(message: types.Message, state: FSMContext):
    """ Если текст сообщения - число """
    async with state.proxy() as data:
        data['amount'] = round(float(message.text), 2)
        tax = get_payment_tax(data['amount'])
        summ = round(data['amount'], 2) + tax
        if 'hash' not in data.keys():
            data['hash'] = get_payment_hash(message.chat.id, data['agrm'])
        text = Texts.payments_online_offer.format(agrm=data['agrm'], amount=data['amount'], balance=data['balance'],
                                                  tax=tax, res=summ)
        await delete_message(message)  # удалить сообщение от пользователя с суммой платежа
        await edit_inline_message(message.chat.id, text, Texts.payments_online_offer.parse_mode,
                                  reply_markup=get_keyboard(keyboards.payment_btn))
        inline_msg = await run_cmd(bot.send_invoice(**get_invoice_params(
            message.chat.id, data['agrm'], data['amount'], tax, data['hash']
        )))
        await PaymentFSM.next()
        if 'payment' not in data.keys():
            await sql.add_payment(data['hash'], message.chat.id, data['agrm'], data['amount'], inline_msg.message_id)
            await alogger.info(f'New payment [{message.chat.id}]')
        else:
            await sql.upd_payment(data['hash'], amount=data['amount'], inline=inline_msg.message_id)
        data['payment'] = dict(chat_id=inline_msg.chat.id, message_id=inline_msg.message_id)


@dp.callback_query_handler(text='payments-online-another-amount', state=PaymentFSM.payment)
async def inline_h_payment_another_amount(query: types.CallbackQuery, state: FSMContext):
    """ Изменение суммы онлайн платежа """
    async with state.proxy() as data:
        await PaymentFSM.amount.set()
        if 'payment' in data.keys():
            await delete_message(data['payment'])
        answer, text, parse = Texts.payments_online_amount.full()
        await update_inline_query(query,
                                  answer.format(agrm=data['agrm']),
                                  text.format(agrm=data['agrm'], balance=data['balance']),
                                  parse,
                                  reply_markup=cancel_menu['inline'])


@dp.pre_checkout_query_handler(lambda query: True, state='*')
async def checkout(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext):
    """ Обработчик для подтверждения платежа - запускается при нажатии на кнопку "Оплатить" """
    payment_hash = pre_checkout_query.invoice_payload
    payment_data = await sql.find_payment(payment_hash)
    if payment_data['status'] in ['finished']:
        ok = False
        msg = Texts.payments_online_already_have
    else:
        ok = True
        msg = Texts.payment_error_message
    await run_cmd(bot.answer_pre_checkout_query(pre_checkout_query.id, ok=ok, error_message=msg))


@dp.message_handler(content_types=types.message.ContentTypes.SUCCESSFUL_PAYMENT, state='*')
@dp.async_task
async def got_payment(message: types.Message, state: FSMContext):
    """
    Обработчик успешного платежа (перевода)

    Telegram Платежи 2.0 не поддерживают передачу данных для Платёжных систем (например, YooKassa),
    чтобы эти системы автоматически проводили пополнение счёта абонента (то есть запрос от YooKassa в LanBilling),
    так как "платежи" здесь являются скорее "переводом средств" (но все равно с формированием чеков).
    Поэтому функционал пополнения счёта Договров был реализован здесь, который выполняется после "получения перевода".

    С платежом в Payload передаётся hash_code записи в БД (iccup.irobot.payments), по нему находятся данные о платеже,
    такие как Договор, Сумма, Время и т.д. По этим данным уже выполняется запрос в систему LanBilling для
    пополнения счёта договра.

    Если hash_code не был распознан, то необходимо вручную провести платёж - запускается протокол
    ручного проведения платежа: уведомляется отдел по работе с клиентами.
    Сотрудники должны сверить входящие платежи в личном кабинете YooKassa, данные о платежах в Биллинге и
    состояние платежа в БД "iccup". И, в случае обнаружения ошибки, они должны провести платёж вручную.
    """
    payment_hash = message.successful_payment.invoice_payload
    payment_receipt = message.successful_payment.provider_payment_charge_id
    payment_data = await sql.find_payment(payment_hash)
    if payment_data:
        extra_payment_upd = {}
        await delete_message(payment_data['chat_id'])
        if message.chat.id == payment_data['chat_id']:
            # оплатил тот же кто и создал платёж
            _, text, parse = Texts.payments_online_success.full()
            await run_cmd(bot.send_message(payment_data['chat_id'], text, parse, reply_markup=main_menu))
        else:
            # оплатил другой пользователь
            extra_payment_upd['user_data'] = ujson.loads(message.from_user.as_json())
            await run_cmd(bot.send_message(
                payment_data['chat_id'], Texts.payments_online_was_paid.format(amount=payment_data['amount']),
                Texts.payments_online_was_paid.parse_mode, reply_markup=main_menu
            ))
            _, text, parse = Texts.payments_online_success_short.full()
            await run_cmd(bot.send_message(message.chat.id, text, parse))
            if not await sql.get_sub(message.chat.id):
                _, text, parse = Texts.payments_after_for_guest.full()
                await run_cmd(bot.send_message(message.chat.id, text, parse))
        try:
            # TODO: agrm to agrm_id !!!
            rec_id = await payment(payment_data['agrm'], payment_data['amount'], payment_receipt, message.date)
        except Exception as e:
            await sql.upd_payment(payment_hash, status='error')
            await alogger.info('Payment Bad attempt [{}]: {}'.format(payment_data['payment_id'], e))
        else:
            await sql.upd_payment(payment_hash, status='finished', record_id=rec_id)#, **extra_payment_upd)
    else:
        await alogger.error(f'Cannot find a payment, strange payment PAYLOAD: "{payment_hash}". Payment receipt: {payment_receipt}')  # ошибка платежа, manual handling required
    if await state.get_state() == PaymentFSM.payment.state:
        await state.finish()


@dp.callback_query_handler(text='yes', state=PaymentFSM.amount)
@dp.async_task
async def inline_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    """ Обещанный платеж """
    async with state.proxy() as data:
        agrm_id = await sql.get_agrm_id(query.message.chat.id, data['agrm'])
        res = await promise_payment(agrm_id, data['amount'])
        if res:
            answer, text, parse = Texts.payments_promise_success.full()
            await alogger.info(f'Payment success [{query.message.chat.id}]')
        else:
            answer, text, parse = Texts.payments_promise_fail.full()
            await alogger.warning(f'Payment failure [{query.message.chat.id}]')
        await update_inline_query(query, answer, text, parse, alert=True)
        await state.finish()
        await run_cmd(bot.send_message(query.message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode,
                                       reply_markup=main_menu))


@dp.callback_query_handler(text='no', state=PaymentFSM.amount)  # обещанный платёж
@dp.callback_query_handler(text='cancel', state=PaymentFSM.states)  # онлайн оплата
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await update_inline_query(query, *Texts.cancel.full(), reply_markup=main_menu)
        if data['operation'] == 'online' and 'hash' in data.keys():
            await sql.upd_payment(data['hash'], status='canceled')
        await state.finish()
