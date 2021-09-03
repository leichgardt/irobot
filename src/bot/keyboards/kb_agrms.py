account_settings_btn = (
    (
        {'text': 'Добавить', 'callback_data': 'add-account'},
        {'text': 'Назад', 'callback_data': 'settings'},
    ),
)


async def get_agrms_btn(chat_id=None, custom=None, prefix='agrm'):
    from src.bot.api import get_all_agrm_data
    rows, row = [], []
    if chat_id:
        data = await get_all_agrm_data(chat_id, only_numbers=True)
    else:
        data = custom
    for agrm in data:
        if isinstance(agrm, dict):
            params = dict(text=str(agrm['agrm']), callback_data='{}-{}'.format(prefix, agrm['agrm']))
        else:
            params = dict(text=str(agrm), callback_data=f'{prefix}-{agrm}')
        row.append(params)
        if len(row) == 2:
            rows.append(tuple(row))
            row = []
    if row:
        rows.append(row)
    return tuple(rows)
