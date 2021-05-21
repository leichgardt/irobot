agrms_settings_btn = (
    (
        {'text': 'Добавить', 'callback_data': 'agrm-add'},
        {'text': 'Назад', 'callback_data': 'settings'},
    ),
)


async def get_agrms_btn(chat_id=None, agrms=None):
    from src.sql import sql
    rows = []
    row = []
    if chat_id:
        data = await sql.get_agrms(chat_id)
    else:
        data = agrms
    for agrm in data:
        params = {'text': str(agrm), 'callback_data': f'agrm-{agrm}'}
        row.append(params)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return tuple(rows)
