account_settings_btn = (
    (
        {'text': 'Добавить', 'callback_data': 'add-account'},
        {'text': 'Назад', 'callback_data': 'settings'},
    ),
)


async def get_agrms_btn(chat_id=None, custom=None, prefix='agrm'):
    from src.sql import sql
    rows, row = [], []
    if chat_id:
        data = await sql.get_agrms(chat_id)
    else:
        data = custom
    for agrm in data:
        params = {'text': str(agrm), 'callback_data': f'{prefix}-{agrm}'}
        row.append(params)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return tuple(rows)
