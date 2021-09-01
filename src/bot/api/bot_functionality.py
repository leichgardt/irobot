import hashlib

from aiogram import types
from datetime import datetime

from src.bot.text import Texts
from src.lb import get_balance
from src.sql import sql
from src.utils import alogger, config


def get_hash(text):
    return hashlib.md5(f'{datetime.now()}&{text}'.encode()).hexdigest()


def get_payment_hash(chat_id, agrmnum):
    return get_hash(f'{chat_id}&{agrmnum}')


def get_payment_price(agrm: str, amount: [int, float], tax: [int, float]):
    return [types.LabeledPrice(label=Texts.payment_item_price.format(agrm=agrm), amount=int(amount * 100)),
            types.LabeledPrice(label=Texts.payment_item_tax, amount=int(tax * 100))]


def get_payment_tax(amount: [int, float]):
    # комиссия до 4%
    mul = 0.03626943005181345792
    return round(amount * mul, 2)


def get_invoice_params(chat_id, agrm, amount, tax, hash_code):
    return dict(
        chat_id=chat_id,
        title=Texts.payment_title.format(agrm=agrm),
        description=Texts.payment_description.format(agrm=agrm, amount=amount),
        provider_token=config['yandex']['telegram-token-test'],  # config['yandex']['telegram-token']
        currency='rub',
        prices=get_payment_price(agrm, amount, tax),
        start_parameter=f'payment-{hash_code}',
        payload=hash_code
    )


def get_login_url(hash_code):
    return 'https://{}/irobot/login?hash={}'.format(config['paladin']['maindomain'], hash_code)


async def get_agrm_balances(chat_id):
    await alogger.info(f'Balance check [{chat_id}]')
    text = []
    agrms = await sql.get_agrms(chat_id)
    if agrms:
        for agrm in agrms:
            bal = await get_balance(agrm)
            if bal:
                summ = round(bal['balance'], 2)
                text.append(Texts.balance.format(agrm=agrm, summ=summ))
                if 'credit' in bal:
                    text[-1] += Texts.balance_credit.format(cre=bal['credit']['sum'],
                                                            date=bal["credit"]["date"].split(' ')[0])
    else:
        text = Texts.balance_no_agrms,
    return '\n'.join(text)
