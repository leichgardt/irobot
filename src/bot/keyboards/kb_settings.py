settings_menu_btn = (
    (
        {'text': 'Мои договоры', 'callback_data': 'settings-my-agrms'},
        {'text': 'Уведомления', 'callback_data': 'settings-notify'},
    ),
    (
        {'text': 'Выйти из программы', 'callback_data': 'exit'},
        {'text': 'Завершить настройки', 'callback_data': 'settings-done'},
    ),
)
exit_confirm_btn = (
    (
        {'text': 'Выйти', 'callback_data': 'exit-yes'},
        {'text': 'Отмена', 'callback_data': 'settings'},
    ),
)
agrm_control_btn = (
    (
        {'text': 'Удалить', 'callback_data': 'agrm-del'},
        {'text': 'Назад', 'callback_data': 'settings-my-agrms'},
    ),
)
cancel_btn = (
    (
        {'text': 'Отмена', 'callback_data': 'cancel'},
    ),
)
back_to_settings = (
    (
        {'text': 'Назад', 'callback_data': 'settings'},
    ),
)
confirm_btn = (
    (
        {'text': 'Да', 'callback_data': 'yes'},
        {'text': 'Нет', 'callback_data': 'no'},
    ),
)
start_r_btn = (
    (
        {'text': '/start'},
    ),
)


async def get_notify_settings_btn(chat_id):
    from src.sql import sql
    row = []
    data = await sql.get_sub(chat_id)
    if data:
        if data[0]:
            text = 'Выкл. рассылку'
        else:
            text = 'Вкл. рассылку'
        params = {'text': text, 'callback_data': 'settings-switch-mailing'}
        row.append(params)
    return (row,)


def get_login_btn(url):
    return (
        (
            {'text': 'Авторизоваться', 'url': url},
        ),
    )
