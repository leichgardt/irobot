from datetime import datetime
import hashlib

from src.bot.text import Texts
from src.lb import get_balance
from src.sql import sql
from src.utils import alogger, config


def get_payment_hash(chat_id, agrmnum):
    line = f'{datetime.now()}&{chat_id}&{agrmnum}'.encode()
    return hashlib.md5(line).hexdigest()


def get_payment_url(hash_code):
    return 'https://{}/irobot/web/api/new_payment?hash={}'.format(config['paladin']['userside'], hash_code)


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
