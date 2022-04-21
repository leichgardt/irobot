from datetime import datetime
from typing import Union, List

import ujson
from aiogram.types import LabeledPrice

from src.bot.core import bot
from src.modules import lb, sql, Texts
from config import BOT_PAYMENT_TOKEN, RECEIPT_EMAIL
from src.utils import get_hash


# async def start_payment(chat_id, payload):
#     """ Отправить счёт, если его собирается оплатить другой пользователь """
#     if payload and 'payment-' in payload:
#         hash_code = payload.replace('payment-', '')
#         payment = await sql.find_payment(hash_code)
#         if payment:
#             if payment['status'] != 'finished':
#                 await bot.send_invoice(**get_invoice_params(
#                     chat_id, payment['agrm'], payment['amount'], get_payment_tax(payment['amount']), hash_code
#                 ))
#             else:
#                 _, text, parse_mode = Texts.payments_online_already_have.full()
#                 await bot.send_message(chat_id, text, parse, reply_markup=keyboards.main_menu_kb)
#         return True
#     return False


def get_payment_hash(chat_id: int, agreement_num: str):
    return get_hash(f'{chat_id}&{agreement_num}')


def get_payment_price(agrm: str, amount: Union[int, float], tax: Union[int, float] = None):
    """ Получить список товаров для онлайн оплаты (Telegram Payments 2.0 - for invoice) """
    tax = [LabeledPrice(label=Texts.payment_item_tax, amount=int(tax * 100))] if tax else []
    return [LabeledPrice(label=Texts.payment_item_price.format(agrm=agrm), amount=int(amount * 100))] + tax


async def get_promise_payment_agrms(agrms: List[str]) -> List[str]:
    """
    Договоры, доступные для обещанного платежа для определённого чата `chat_id` или из предоставленного списка `agrms`
    """
    output = []
    if agrms:
        for agrm in agrms:
            if await lb.promise_available(agrm):
                output.append(agrm)
    return output


async def send_payment_invoice(chat_id: int, hash_code: str, agreement: str, amount: int, payload: dict):
    return await bot.send_invoice(
        chat_id,
        provider_token=BOT_PAYMENT_TOKEN,
        provider_data=dict(
            tax_system_code=0,
            customer=dict(
                email=RECEIPT_EMAIL,
            ),
            items=[dict(
                description=Texts.payment_description.format(agrm=agreement, amount=amount),
                quantity='1.0',
                amount=dict(
                    value=amount * 100,
                    currency='RUB'
                ),
                vat_code=1,
            ), ],
        ),
        title=Texts.payment_title,
        description=Texts.payment_description_item.format(agrm=agreement, amount=amount),
        currency='RUB',
        prices=get_payment_price(agreement, amount),
        payload=ujson.dumps(payload),
        start_parameter=f'payment-{hash_code}',
    )


async def make_payment(
        agrm_num: str,
        amount: int,
        receipt: str,
        hash_code: str,
        payment_date: Union[str, datetime] = None,
        test: bool = False
) -> int:
    params = {'receipt': receipt}
    # пополнить баланс на оплаченную сумму
    record_id = await lb.new_payment(agrm_num, amount, receipt, payment_date, test=test)
    if record_id:
        params['record_id'] = record_id
        params['status'] = 'success'
    else:
        params['status'] = 'processing'
    await sql.upd_payment(hash_code, **params)
    return record_id
