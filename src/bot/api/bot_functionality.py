from aiogram.utils.emoji import emojize

from src.sql import sql
from src.lb import get_balance


async def get_agrm_balances(chat_id):
    text = []
    agrms = await sql.get_agrms(chat_id)
    if agrms:
        for agrm in agrms:
            bal = await get_balance(agrm)
            if bal:
                summ = round(bal['balance'], 2)
                text.append(f'Баланс договора №{agrm}:\n{summ} руб.\n')
                if 'credit' in bal:
                    date = bal["credit"]["date"].split(' ')
                    text[-1] += f'Обещанный платёж:\n{bal["credit"]["sum"]} руб. до {date[0]}\n'
    else:
        text = 'У тебя удалены все договоры. Добавь их в Настройках Договоров /settings',
    return emojize('\n'.join(text))


if __name__ == '__main__':
    async def main():
        res = await get_agrm_balances(0)
        print(res)
    import uvloop, asyncio
    loop = uvloop.new_event_loop()
    loop.run_until_complete(main())
