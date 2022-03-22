from ..api.keyboard_button import KeyboardButton
from ...sql import sql


__all__ = [
    'settings_menu_btn',
    'exit_confirm_btn',
    'account_control_btn',
    'cancel_btn',
    'confirm_btn',
    'get_notify_settings_btn',
    'get_login_btn'
]


settings_menu_btn = [
    [
        KeyboardButton('Учётные записи', callback_data='settings-my-accounts'),
        KeyboardButton('Уведомления', callback_data='settings-notify')
    ],
    [
        KeyboardButton('Выйти из программы', callback_data='exit'),
        KeyboardButton('Завершить настройки', callback_data='settings-done')
    ],
]

exit_confirm_btn = [
    KeyboardButton('Выйти', callback_data='exit-yes'),
    KeyboardButton('Отмена', callback_data='settings')
]

account_control_btn = [
    KeyboardButton('Удалить', callback_data='del-account'),
    KeyboardButton('Назад', callback_data='settings-my-accounts')
]

cancel_btn = [
    KeyboardButton('Отмена', callback_data='cancel')
]

confirm_btn = [
    KeyboardButton('Да', callback_data='yes'),
    KeyboardButton('Нет', callback_data='no')
]


async def get_notify_settings_btn(chat_id):
    data = await sql.get_sub(chat_id)
    if data:
        if data[0]:
            res = [KeyboardButton('Выкл. рассылку', callback_data='settings-switch-mailing')]
        else:
            res = [KeyboardButton('Вкл. рассылку', callback_data='settings-switch-mailing')]
        return res + [KeyboardButton('Назад', callback_data='settings')]
    else:
        raise ValueError(f'Chat not found [{chat_id}]')


def get_login_btn(url):
    return [
        KeyboardButton('Авторизоваться', url=url)
    ]
