import ujson
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp
from aiogram.utils.emoji import emojize

from src.bot.api import *
from src.bot.schemas import keyboards, Keyboard, KeyboardButton
from src.bot.schemas.fsm_states import PaymentFSM
from src.bot.utils import agreements, payments
from src.modules import lb, sql, Texts
from src.utils import logger

from .l3_main import bot, dp


# _______________ Выбор Типа платежа и договора _______________

@dp.message_handler(Text(emojize(':moneybag: Платежи')), state='*')
@private_and_login_require()
@exc_handler
async def message_h_payments(message: types.Message, state: FSMContext):
    await state.finish()
    await PaymentFSM.operation.set()
    res = await bot.send_message(message.chat.id, *Texts.payments.pair(), reply_markup=keyboards.payment_choice_kb)
    await sql.upd_inline_message(message.chat.id, res.message_id, *Texts.payments.pair())


@dp.callback_query_handler(text='payments', state=PaymentFSM.states)
@exc_handler
async def inline_h_payments(query: types.CallbackQuery, state: FSMContext):
    await PaymentFSM.operation.set()
    await update_inline_query(query, *Texts.payments.full(), reply_markup=keyboards.payment_choice_kb)


@dp.callback_query_handler(text='payments-online', state=PaymentFSM.states)
@exc_handler
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Оплата онлайн
    Отправляет сообщение с выбором договра, если их несколько, иначе отправляет окно ввода суммы патежа
    """
    # await query.answer('Мы работаем над этим. Сейчас эта функция в разработке', show_alert=True)
    async with state.proxy() as data:
        data['operation'] = 'online'
        data['agrm_data'] = await agreements.get_all_agrm_data(query.message.chat.id)
        if len(data['agrm_data']) == 0:
            await state.finish()
            answer, text, parse_mode = Texts.balance_no_agrms.full()
            kb = keyboards.main_menu_kb
        elif len(data['agrm_data']) == 1:
            await PaymentFSM.amount.set()
            data['agrm'] = data['agrm_data'][0]['agrm']
            answer, text, parse_mode = Texts.payments_online_amount.full(agrm=data['agrm'])
            kb = Keyboard(keyboards.back_to_payments_btn).inline()
        else:
            await PaymentFSM.agrm.set()
            answer, text, parse_mode = Texts.payments_online.full()
            kb = Keyboard([await keyboards.get_agrms_btn(custom=data['agrm_data']),
                           keyboards.back_to_payments_btn]).inline()
        await update_inline_query(query, answer, text, parse_mode, reply_markup=kb)


@dp.callback_query_handler(text='payments-promise', state=PaymentFSM.states)
@dp.async_task
@exc_handler
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Обещанный платёж. Функция проверяет к каким договорам можно подключить обещанный платёж, и показывает только их.
    """
    async with state.proxy() as data:
        if query.data == 'payments-promise':
            data['operation'] = 'promise'
            data['agrm_data'] = await agreements.get_all_agrm_data(query.message.chat.id)
            data['amount'] = 100
        if len(data['agrm_data']) == 0:
            await state.finish()
            answer, text, parse_mode = Texts.balance_no_agrms.full()
            kb = keyboards.main_menu_kb
        else:
            agrms = await payments.get_promise_payment_agrms(data['agrm_data'])
            if len(agrms) == 1:
                await PaymentFSM.payment.set()
                data['agrm'] = agrms[0]['agrm']
                answer, text, parse_mode = Texts.payments_promise_offer.full()
                kb = Keyboard(keyboards.confirm_btn).inline()
                answer = answer.format(agrm=data['agrm'])
                text = text.format(agrm=data['agrm'])
            elif len(agrms) > 1:
                await PaymentFSM.agrm.set()
                answer, text, parse_mode = Texts.payments_promise.full()
                kb = Keyboard([await keyboards.get_agrms_btn(custom=agrms), keyboards.back_to_payments_btn]).inline()
            else:
                await state.finish()
                answer, text, parse_mode = Texts.payments_promise_already_have.full()
                kb = Keyboard(keyboards.payment_choice_kb).inline()
        await update_inline_query(query, answer, text, parse_mode, reply_markup=kb)


@dp.callback_query_handler(Regexp(regexp=r'agrm-([^\s]*)'), state=PaymentFSM.agrm)
@exc_handler
async def inline_h_payments_agrm(query: types.CallbackQuery, state: FSMContext):
    """
    Выбор договора для платежа
    Возвращает сообщение с вводом суммы (при онлайн оплате) или с выбором Да/Нет на обещанный платёж
    """
    async with state.proxy() as data:
        data['agrm'] = query.data[5:] if 'agrm-' in query.data else data['agrm']
        if data['operation'] == 'promise':
            await PaymentFSM.payment.set()
            answer, text, parse_mode = Texts.payments_promise_offer.full()
            kb = Keyboard(keyboards.confirm_btn).inline()
        else:
            await PaymentFSM.amount.set()
            answer, text, parse_mode = Texts.payments_online_amount.full()
            kb = Keyboard([KeyboardButton(Texts.back, callback_data='payments-online')]).inline()
        answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        await update_inline_query(query, answer, text, parse_mode, reply_markup=kb)


# _______________ Обещанный платёж _______________

@dp.callback_query_handler(text='yes', state=PaymentFSM.payment)
@dp.async_task
@exc_handler
async def inline_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    """ Обещанный платеж """
    async with state.proxy() as data:
        agrm_id = [agrm['agrm_id'] for agrm in data['agrm_data'] if agrm['agrm'] == data['agrm']]
        if not agrm_id:
            await logger.error(f'Promise payment error! Cannot get agrm_id from agrm "{data["agrm"]}": '
                               f'{data["agrm_data"]}')
            await bot.send_message(query.message.chat.id, *Texts.backend_error.pair(),
                                   reply_markup=keyboards.main_menu_kb)
        else:
            res = await lb.promise_payment(agrm_id[0], data['amount'])
            if res:
                answer, text, parse_mode = Texts.payments_promise_success.full()
                await logger.info(f'Promise Payment success [{query.message.chat.id}]')
            else:
                answer, text, parse_mode = Texts.payments_promise_fail.full()
                await logger.warning(f'Payment failure [{query.message.chat.id}]')
            await update_inline_query(query, answer, text, parse_mode, alert=True)
            text, parse_mode = await agreements.get_agrm_balances(query.message.chat.id)
            await bot.send_message(query.message.chat.id, text, parse_mode, reply_markup=keyboards.main_menu_kb)
        await state.finish()


@dp.callback_query_handler(text='no', state=PaymentFSM.payment)
@exc_handler
async def inline_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    await update_inline_query(query, *Texts.payments.full(), reply_markup=keyboards.payment_choice_kb)


# _______________ Онлайн оплата _______________

@dp.message_handler(lambda message: not message.text.isdigit() or (message.text.isdigit() and int(message.text) < 100),
                    state=PaymentFSM.amount)
@exc_handler
async def inline_h_payment_non_int(message: types.Message, state: FSMContext):
    """ Если текст сообщения НЕ число или меньше минимума - попросить ввести ещё раз """
    async with state.proxy() as data:
        if len(data['agrm_data']) > 1:
            btn = KeyboardButton(Texts.back, callback_data='payments-online')
        else:
            btn = KeyboardButton(Texts.back, callback_data='payments')
        if not message.text.isdigit():
            text, parse_mode = Texts.payments_online_amount_is_not_digit.pair()
        else:
            text, parse_mode = Texts.payments_online_amount_is_too_small.pair()
        await edit_inline_message(message.chat.id, text, parse_mode, btn_list=[btn])
        await delete_message(message)


@dp.message_handler(lambda message: message.text.isdigit() and int(message.text) >= 100, state=PaymentFSM.amount)
@exc_handler
async def inline_h_payment(message: types.Message, state: FSMContext):
    """ Если текст сообщения Число или больше минимума - выдать счёт на оплату """
    async with state.proxy() as data:
        await state.finish()
        amount = int(message.text)
        hash_code = payments.get_payment_hash(message.chat.id, data['agrm'])
        payload = {'hash': hash_code, 'chat_id': message.chat.id, 'agrm': data['agrm'], 'amount': amount}
        await bot.send_chat_action(message.chat.id, 'typing')
        await delete_message(message.chat.id)  # delete bot message
        await delete_message(message)  # delete user message
        await payments.send_payment_invoice(message.chat.id, hash_code, data['agrm'], amount, payload)


@dp.pre_checkout_query_handler(lambda query: True, state='*')
@exc_handler
async def checkout(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext):
    """ Обработчик для подтверждения транзакции - запускается при нажатии на кнопку "Оплатить" """
    await logger.info(f'[{pre_checkout_query.from_user.id}] Pre-payment checkout {pre_checkout_query.invoice_payload}')
    ok = False
    msg = Texts.payment_error_message
    data = eval(pre_checkout_query.invoice_payload)
    if data.get('hash') and data.get('agrm') and data.get('amount'):
        payment = await sql.find_payment(data['hash'])
        if not payment:
            payment_id = await sql.add_payment(data['hash'], data['chat_id'], data['agrm'], data['amount'],
                                               status='processing')
            ok = True if payment_id > 0 else False
        elif payment['status'] == 'new':
            await sql.upd_payment(data['hash'], status='processing')
            ok = True
        elif payment['status'] == 'processing':
            msg = Texts.payments_online_already_processing
        elif payment['status'] == 'success':
            msg = Texts.payments_online_already_have
        elif payment['status'] == 'canceled':
            msg = Texts.payments_online_already_canceled
    await logger.info(f'[{pre_checkout_query.from_user.id}] Pre-payment status {ok=}')
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=ok, error_message=msg)


@dp.message_handler(content_types=types.message.ContentTypes.SUCCESSFUL_PAYMENT, state='*')
@dp.async_task
@exc_handler
async def got_payment(message: types.Message, state: FSMContext):
    """
    Обработчик успешного платежа (перевода) через invoice.
    Запускается при подтверждении перевода от платёжного провайдера.
    Пополняет баланс абонента на оплаченную сумму.
    """
    TEST = False
    # params - первоначальные данные для обновления платежа в БД
    params = {'receipt': message.successful_payment.provider_payment_charge_id, 'status': 'error'}
    data = eval(message.successful_payment.invoice_payload)
    if data.get('hash') and data.get('agrm') and data.get('amount'):
        # пополнить баланс на оплаченную сумму
        record_id = await lb.new_payment(data['agrm'], data['amount'], params['receipt'], message.date, test=TEST)
        if record_id:
            await logger.info(f'[{data["chat_id"]}] Successful Payment: {record_id=} receipt={params["receipt"]}')
            params['record_id'] = record_id
            params['status'] = 'completed'
            text, parse_mode = Texts.payments_online_success_short.pair()
        else:
            await logger.warning(f'[{data["chat_id"]}] Bad payment. Cannot top up the agreement balance: {record_id=} '
                                 f'number={data["agrm"]} amount={data["amount"]} receipt={params["receipt"]}')
            text, parse_mode = Texts.payments_online_success.pair()
        kb = keyboards.main_menu_kb if message.chat.id == data['chat_id'] else None
        await bot.send_message(message.chat.id, text, parse_mode, reply_markup=kb)
        if message.chat.id != data['chat_id']:
            # оплатил другой пользователь
            params['payer'] = ujson.loads(message.from_user.as_json())
            await bot.send_message(data['chat_id'], *Texts.payments_online_was_paid.pair())
            await bot.send_message(message.chat.id, *Texts.payments_after_for_guest.pair())
    else:
        await logger.error(f'[{data["chat_id"]}] Cannot read a payment payload. Receipt={params["receipt"]} '
                           f'Payload={message.successful_payment.invoice_payload}')
    await sql.upd_payment(data['hash'], **params)
