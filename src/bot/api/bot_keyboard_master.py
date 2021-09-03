from aiogram.utils.emoji import emojize
from aiogram import types


def get_btn_params(btn: dict):
    payload = {}
    for key, value in btn.items():
        payload.update({key: emojize(value) if key == 'text' else value})
    return payload


def recursive_add(keyboard, cur_row, new_item, btn_type, row_size=2, lining=False):
    if isinstance(new_item, dict):
        params = get_btn_params(new_item)
        if len(cur_row) == row_size:
            keyboard.row(*cur_row)
            cur_row = [btn_type(**params)]
        else:
            cur_row.append(btn_type(**params))
    elif lining and new_item and isinstance(new_item[0], dict):
        row = []
        for btn in new_item:
            params = get_btn_params(btn)
            row.append(btn_type(**params))
            if len(row) == row_size:
                keyboard.row(*row)
                row = []
        if row:
            keyboard.row(*row)
    else:
        for new_params in new_item:
            cur_row = recursive_add(keyboard, cur_row, new_params, btn_type, row_size, lining)
    return cur_row


def get_keyboard(*args, keyboard_type='inline', lining=True, row_size=2, **kwargs):
    if keyboard_type == 'reply':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, **kwargs)  # one_time_keyboard = True
        btn = types.KeyboardButton
    else:
        kb = types.InlineKeyboardMarkup(**kwargs)
        btn = types.InlineKeyboardButton
    if lining:
        for item in args:
            row = []
            row = recursive_add(kb, row, item, btn, row_size=row_size, lining=True)
            kb.row(*row)
    else:
        row = []
        for item in args:
            row = recursive_add(kb, row, item, btn, row_size=row_size)
        if row:
            kb.row(*row)
    return kb


def get_custom_button(text: str, query_path: str):
    return (dict(text=text, callback_data=query_path),),
