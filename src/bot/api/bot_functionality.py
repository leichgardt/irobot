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


def get_payment_url(hash_code):
    return 'https://{}/irobot/api/new_payment?hash={}'.format(config['paladin']['maindomain'], hash_code)


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
