from src.modules import lb, sql, Texts
from src.utils import logger


async def get_agrm_balances(chat_id: int):
    """ Получить текст с балансом всех договоров для пользователя """
    await logger.info(f'Balance check [{chat_id}]')
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
    return '\n'.join(text), Texts.balance.parse_mode


async def get_all_agrm_data(chat_id: int, *, only_numbers=False):
    """
    Получить список всех договоров (только номера договоров или полные данные)
    :param chat_id: ID чата.
    :param only_numbers: вывести только номера договоров без загрузки полной информации о них.
    """
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
