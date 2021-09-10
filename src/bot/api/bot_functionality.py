import hashlib

from aiogram import types
from datetime import datetime

from src.text import Texts
from src.lb import lb
from src.sql import sql
from src.utils import alogger, config


def get_hash(text):
    """ Получить хэш-код из текста """
    return hashlib.md5(f'{datetime.now()}&{text}'.encode()).hexdigest()


def get_payment_hash(chat_id, agrmnum):
    """ Получить хэш-код для платежа """
    return get_hash(f'{chat_id}&{agrmnum}')


def get_payment_price(agrm: str, amount: [int, float], tax: [int, float]):
    """ Получить список товаров для онлайн оплаты (Telegram Payments 2.0 - for invoice) """
    return [types.LabeledPrice(label=Texts.payment_item_price.format(agrm=agrm), amount=int(amount * 100)),
            types.LabeledPrice(label=Texts.payment_item_tax, amount=int(tax * 100))]


def get_payment_tax(amount: [int, float]):
    """ Рассчитать комиссию для YooKassa (до 4%) """
    mul = 0.03626943005181345792
    return round(amount * mul, 2)


def get_invoice_params(chat_id, agrm, amount, tax, hash_code):
    """ Получить параметры объекта платежа Invoice `bot.send_invoice(**params)` """
    return dict(
        chat_id=chat_id,
        title=Texts.payment_title.format(agrm=agrm),
        description=Texts.payment_description.format(agrm=agrm, amount=amount),
        provider_token=config['yandex']['telegram-token'],
        # provider_token=config['yandex']['telegram-token-test'],
        currency='rub',
        prices=get_payment_price(agrm, amount, tax),
        start_parameter=f'payment-{hash_code}',
        payload=hash_code
    )


def get_login_url(hash_code):
    """ Получить URL для авторизации """
    return 'https://{}/irobot/login?hash={}'.format(config['paladin']['maindomain'], hash_code)
    # return 'http://0.0.0.0:8000/login?hash={}'.format(hash_code)


async def get_agrm_balances(chat_id):
    """ Получить текст с балансом всех договоров для пользователя """
    await alogger.info(f'Balance check [{chat_id}]')
    text = []
    data = await get_all_agrm_data(chat_id, only_numbers=True)
    if data:
        for agrms in data.values():
            for agrm in agrms:
                bal = await lb.get_balance(agrmnum=agrm)
                if bal:
                    text.append(Texts.balance.format(agrm=agrm, summ=bal['balance']))
                    if 'credit' in bal:
                        text[-1] += Texts.balance_credit.format(cre=bal['credit']['sum'],
                                                                date=bal["credit"]["date"].split(' ')[0])
    else:
        text = Texts.balance_no_agrms,
    return '\n'.join(text)


async def get_all_agrm_data(chat_id, *, only_numbers=False):
    """ Получить список всех договоров (только номера договоров или полные данные) """
    output = {}
    accounts = await sql.get_accounts(chat_id)
    for account in accounts:
        agrms = await lb.get_account_agrms(account)
        for agrm in agrms:
            if only_numbers:
                output[account] = [agrm['agrm'] for agrm in agrms]
            else:
                output[agrm['agrm_id']] = agrm
    return output if only_numbers else list(output.values())


async def get_promise_payment_agrms(*, chat_id: int = None, agrms: list = None):
    """
    Договоры, доступные для обещанного платежа для определённого чата `chat_id` или из предоставленного списка `agrms`
    """
    output = []
    if chat_id:
        agrms = []
        accounts = await sql.get_accounts(chat_id)
        for account in accounts:
            agrms += await lb.get_account_agrms(account)
    if agrms:
        for agrm in agrms:
            if await lb.promise_available(agrm):
                output.append(agrm)
    return output
