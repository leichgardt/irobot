import ujson

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.bot import keyboards
from src.bot.api import (main_menu, edit_inline_message, update_inline_query, get_keyboard, delete_message,
                         private_and_login_require, get_payment_hash, run_cmd, get_invoice_params, get_payment_tax,
                         get_all_agrm_data, get_promise_payment_agrms, get_agrm_balances, get_custom_button)
from src.text import Texts
from src.lb import lb
from src.sql import sql
from src.utils import alogger, map_format

from .l3_main import bot, dp


class PaymentFSM(StatesGroup):
    # доп. данные
    hash = State()
    agrm_data = State()
    balance = State()
    # этапы
    operation = State()
    agrm = State()
    amount = State()
    payment = State()


# _______________ Выбор Типа платежа и договора _______________

@dp.message_handler(Text(emojize(':moneybag: Платежи')), state='*')
@private_and_login_require()
async def message_h_payments(message: types.Message, state: FSMContext):
    await state.finish()
    await PaymentFSM.operation.set()
    kb = get_keyboard(keyboards.payment_choice_btn, keyboard_type='inline')
    res = await run_cmd(bot.send_message(message.chat.id, *Texts.payments.pair(), reply_markup=kb))
    await sql.upd_inline(message.chat.id, res.message_id, *Texts.payments.pair())


@dp.callback_query_handler(text='payments', state=PaymentFSM.states)
async def inline_h_payments(query: types.CallbackQuery, state: FSMContext):
    await PaymentFSM.operation.set()
    kb = get_keyboard(keyboards.payment_choice_btn)
    await update_inline_query(query, *Texts.payments.full(), reply_markup=kb)


@dp.callback_query_handler(text='payments-online', state=PaymentFSM.states)
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Оплата онлайн
    Отправляет сообщение с выбором договра, если их несколько, иначе отправляет окно ввода суммы патежа
    """
    async with state.proxy() as data:
        data['operation'] = 'online'
        data['agrm_data'] = await get_all_agrm_data(query.message.chat.id)
        if len(data['agrm_data']) == 0:
            await state.finish()
            answer, text, parse = Texts.balance_no_agrms.full()
            kb = main_menu
        elif len(data['agrm_data']) == 1:
            await PaymentFSM.amount.set()
            data['agrm'] = data['agrm_data'][0]['agrm']
            answer, text, parse = Texts.payments_online_amount.full()
            res = await lb.get_balance(agrm_data=data['agrm_data'][0])
            data['balance'] = res['balance']
            text = map_format(text, balance=data['balance'])
            kb = get_keyboard(keyboards.back_to_payments_btn)
            answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        else:
            await PaymentFSM.agrm.set()
            answer, text, parse = Texts.payments_online.full()
            kb = get_keyboard(await keyboards.get_agrms_btn(custom=data['agrm_data']), keyboards.back_to_payments_btn)
        await update_inline_query(query, answer, text, parse, reply_markup=kb)


@dp.callback_query_handler(text='no', state=PaymentFSM.payment)
@dp.callback_query_handler(text='payments-promise', state=PaymentFSM.states)
@dp.async_task
async def inline_h_payments_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Обещанный платёж

    Функция проверяет к каким договорам можно подключить обещанный платёж, и показывает только их.
    """
    async with state.proxy() as data:
        if query.data == 'payments-promise':
            data['operation'] = 'promise'
            data['agrm_data'] = await get_all_agrm_data(query.message.chat.id)
            data['amount'] = 100
        if len(data['agrm_data']) == 0:
            await state.finish()
            answer, text, parse = Texts.balance_no_agrms.full()
            kb = main_menu
        else:
            agrms = await get_promise_payment_agrms(agrms=data['agrm_data'])
            if len(agrms) == 1:
                await PaymentFSM.payment.set()
                data['agrm'] = agrms[0]['agrm']
                answer, text, parse = Texts.payments_promise_offer.full()
                kb = get_keyboard(keyboards.confirm_btn)
                answer = answer.format(agrm=data['agrm'])
                text = text.format(agrm=data['agrm'])
            elif len(agrms) > 1:
                await PaymentFSM.agrm.set()
                answer, text, parse = Texts.payments_promise.full()
                kb = get_keyboard(await keyboards.get_agrms_btn(custom=agrms), keyboards.back_to_payments_btn)
            else:
                await state.finish()
                answer, text, parse = Texts.payments_promise_already_have.full()
                kb = get_keyboard(keyboards.payment_choice_btn)
        await update_inline_query(query, answer, text, parse, reply_markup=kb)


@dp.callback_query_handler(Regexp(regexp=r'agrm-([^\s]*)'), state=PaymentFSM.agrm)
async def inline_h_payments_agrm(query: types.CallbackQuery, state: FSMContext):
    """
    Выбор договора для платежа
    Возвращает сообщение с вводом суммы (при онлайн оплате) или с выбором Да/Нет на обещанный платёж
    """
    async with state.proxy() as data:
        data['agrm'] = query.data[5:] if 'agrm-' in query.data else data['agrm']
        if data['operation'] == 'promise':
            await PaymentFSM.payment.set()
            answer, text, parse = Texts.payments_promise_offer.full()
            kb = get_keyboard(keyboards.confirm_btn)
        else:
            await PaymentFSM.amount.set()
            answer, text, parse = Texts.payments_online_amount.full()
            balance = await lb.get_balance(agrmnum=data['agrm'])
            data['balance'] = balance['balance']
            text = map_format(text, balance=data['balance'])
            kb = get_keyboard(get_custom_button(Texts.back, 'payments-online'))
        answer, text = answer.format(agrm=data['agrm']), text.format(agrm=data['agrm'])
        await update_inline_query(query, answer, text, parse, reply_markup=kb)


# _______________ Обещанный платёж _______________

@dp.callback_query_handler(text='yes', state=PaymentFSM.payment)
@dp.async_task
async def inline_h_payment_yes(query: types.CallbackQuery, state: FSMContext):
    """ Обещанный платеж """
    async with state.proxy() as data:
        agrm_id = [agrm['agrm_id'] for agrm in data['agrm_data'] if agrm['agrm'] == data['agrm']]
        if not agrm_id:
            await alogger.error(f'Promise payment error! Cannot get agrm_id from agrm "{data["agrm"]}": {data["agrm_data"]}')
            await run_cmd(bot.send_message(query.message.chat.id, *Texts.backend_error.pair(), reply_markup=main_menu))
        else:
            res = await lb.promise_payment(agrm_id[0], data['amount'])
            if res:
                answer, text, parse = Texts.payments_promise_success.full()
                await alogger.info(f'Promise Payment success [{query.message.chat.id}]')
            else:
                answer, text, parse = Texts.payments_promise_fail.full()
                await alogger.warning(f'Payment failure [{query.message.chat.id}]')
            text = await get_agrm_balances(query.message.chat.id)
            await update_inline_query(query, answer, text, parse, alert=True)
            await run_cmd(bot.send_message(query.message.chat.id, text, Texts.balance.parse_mode,
                                           reply_markup=main_menu))
        await state.finish()


# _______________ Онлайн оплата _______________

@dp.message_handler(lambda message: not message.text.isdigit(), state=PaymentFSM.amount)
async def inline_h_payment(message: types.Message, state: FSMContext):
    """ Если текст сообщения НЕ число - попросить ввести ещё раз """
    async with state.proxy() as data:
        if len(data['agrm_data']) > 1:
            kb = get_custom_button(Texts.back, 'payments-online')
        else:
            kb = get_custom_button(Texts.back, 'payments')
        await edit_inline_message(message.chat.id, *Texts.payments_online_amount_is_not_digit.pair(), kb)
        await delete_message(message)


@dp.message_handler(lambda message: message.text.isdigit(), state=PaymentFSM.amount)
async def inline_h_payment(message: types.Message, state: FSMContext):
    """ Если текст сообщения Число - выдать счёт на оплату """
    async with state.proxy() as data:
        await PaymentFSM.payment.set()
        data['amount'] = round(float(message.text), 2)
        tax = get_payment_tax(data['amount'])
        summ = round(data['amount'], 2) + tax
        if 'hash' not in data.keys():
            data['hash'] = get_payment_hash(message.chat.id, data['agrm'])
        await delete_message(message)  # удалить сообщение от пользователя с суммой платежа
        await edit_inline_message(
            message.chat.id,
            *Texts.payments_online_offer.pair(agrm=data['agrm'], amount=data['amount'], balance=data['balance'],
                                              tax=tax, res=summ),
            reply_markup=get_keyboard(keyboards.payment_btn)
        )
        inline_msg = await run_cmd(bot.send_invoice(**get_invoice_params(
            message.chat.id, data['agrm'], data['amount'], tax, data['hash']
        )))
        if 'payment' not in data.keys():
            payment_id = await sql.add_payment(data['hash'], message.chat.id, data['agrm'], data['amount'],
                                               inline_msg.message_id)
            await alogger.info(f'New payment [{message.chat.id}]: ID={payment_id}')
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
        answer, text, parse = Texts.payments_online_amount.full(agrm=data['agrm'], balance=data['balance'])
        await update_inline_query(query, answer, text, parse,
                                  reply_markup=get_keyboard(get_custom_button(Texts.back, 'payments-online')))


@dp.callback_query_handler(text='cancel', state=PaymentFSM.payment)  # онлайн оплата
async def inline_h_payments_cancel(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await PaymentFSM.operation.set()
        if 'operation' in data.keys() and data['operation'] == 'online' and 'hash' in data.keys():
            res = await sql.find_payment(data['hash'])
            if res:
                await delete_message((query.message.chat.id, res['inline']))
            await sql.upd_payment(data['hash'], status='canceled')
        await update_inline_query(query, *Texts.payments.full(),
                                  reply_markup=get_keyboard(keyboards.payment_choice_btn))


@dp.pre_checkout_query_handler(lambda query: True, state='*')
async def checkout(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext):
    """ Обработчик для подтверждения платежа - запускается при нажатии на кнопку "Оплатить" """
    ok = False
    msg = Texts.payment_error_message
    payment_hash = pre_checkout_query.invoice_payload
    if payment_hash:
        payment = await sql.find_payment(payment_hash)
        if payment:
            if payment['status'] in ['success', 'canceled', 'processing', 'error', 'failure', 'timed_out']:
                ok = False
                if payment['status'] == 'success':
                    msg = Texts.payments_online_already_have
                elif payment['status'] == 'canceled':
                    msg = Texts.payments_online_already_canceled
                elif payment['status'] == 'processing':
                    msg = Texts.payments_online_already_processing
            else:
                ok = True
                await sql.upd_payment(payment_hash, status='processing')
    await run_cmd(bot.answer_pre_checkout_query(pre_checkout_query.id, ok=ok, error_message=msg))


@dp.message_handler(content_types=types.message.ContentTypes.SUCCESSFUL_PAYMENT, state='*')
@dp.async_task
async def got_payment(message: types.Message, state: FSMContext):
    """
    Обработчик успешного платежа (перевода)

    Telegram Платежи 2.0 не поддерживают передачу данных напрямую в Платёжную систему (например, customerID), чтобы
    эта система автоматически проводила пополнение счёта абонента (то есть посылала запрос на LanBilling),
    так как "платёж" здесь является скорее "переводом средств" (но все равно с формированием чека). Поэтому функционал
    пополнения счётов Договоров был реализован здесь, который выполняется после получения "успешного перевода".

    Вместе с SUCCESSFUL_PAYMENT в Payload передаётся hash_code платежа (записи в БД iccup: irobot.payments), по нему
    находятся сохранённые данные о платеже, такие как Номер Договора, Сумма, Время создания и т.д. По этим данным
    уже выполняется API-запрос в систему LanBilling для пополнения счёта договора.

    Если hash_code не был распознан, то необходимо вручную провести платёж, так как средства поступили, а платёж
    определить не удастся. Поэтому запускается протокол ручного проведения платежа: уведомляется отдел по работе
    с клиентами.
    Сотрудники должны сверить входящие платежи в личном кабинете YooKassa и состояние платежа в БД "iccup".
    И, в случае обнаружения ошибки, они должны провести платёж вручную или вернуть средства.
    """
    # params - первоначальные данные для обновления платежа в БД
    params = dict(receipt=message.successful_payment.provider_payment_charge_id, status='error')
    payment_hash = message.successful_payment.invoice_payload
    if payment_hash:
        payment = await sql.find_payment(payment_hash)
        if payment:
            await delete_message(payment['chat_id'])
            if message.chat.id == payment['chat_id']:
                # оплатил тот же кто и создал платёж
                if await state.get_state() == PaymentFSM.payment.state:
                    await state.finish()
                text, parse = Texts.payments_online_success.pair()
                await run_cmd(bot.send_message(payment['chat_id'], text, parse, reply_markup=main_menu))
            else:
                # оплатил другой пользователь
                params['payer'] = ujson.loads(message.from_user.as_json())
                await run_cmd(bot.send_message(
                    payment['chat_id'], *Texts.payments_online_was_paid.pair(amount=payment['amount']),
                    reply_markup=main_menu
                ))
                text, parse = Texts.payments_online_success_short.pair()
                await run_cmd(bot.send_message(message.chat.id, text, parse))
                if not await sql.get_sub(message.chat.id):
                    text, parse = Texts.payments_after_for_guest.pair()
                    await run_cmd(bot.send_message(message.chat.id, text, parse))
            rec_id = await lb.new_payment(payment['agrm'], payment['amount'], params['receipt'], message.date)
            if rec_id:
                params['status'] = 'success'
                params['record_id'] = rec_id
                await alogger.info(f'Successful Payment: ID={payment["id"]}')
            else:
                await alogger.info(f'Bad Payment: ID={payment["id"]}')
        else:
            await alogger.error(f'Cannot find a payment. Payment receipt: {params["receipt"]}')
        await sql.upd_payment(payment_hash, **params)
    else:
        await alogger.error(f'Cannot find a payment, strange payment PAYLOAD: "{payment_hash}". '
                            f'Payment receipt: {params["receipt"]}')
