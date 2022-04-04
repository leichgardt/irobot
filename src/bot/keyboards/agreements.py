from src.bot.api.functions import get_all_agrm_data
from src.bot.api.keyboard import KeyboardButton


__all__ = ('account_settings_btn', 'get_agrms_btn')


account_settings_btn = [
    KeyboardButton('Добавить', callback_data='add-account'),
    KeyboardButton('Назад', callback_data='settings'),
]


async def get_agrms_btn(chat_id=None, custom=None, prefix='agrm'):
    rows, row = [], []
    if chat_id:
        data = await get_all_agrm_data(chat_id, only_numbers=True)
    else:
        data = custom
    for agrm in data:
        if isinstance(agrm, dict):
            button = KeyboardButton(str(agrm['agrm']), callback_data=f'{prefix}-{agrm["agrm"]}')
        else:
            button = KeyboardButton(str(agrm), callback_data=f'{prefix}-{agrm}')
        row.append(button)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows
