from aiogram.utils.emoji import emojize

from src.sql import sql
from src.lb import get_balance
from src.bot.text import Texts
from src.utils import alogger


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
    return emojize('\n'.join(text))


if __name__ == '__main__':
    async def main():
        res = await get_agrm_balances(0)
        print(res)
    import uvloop, asyncio
    loop = uvloop.new_event_loop()
    loop.run_until_complete(main())
