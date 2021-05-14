from src.sql import sql

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
notify_settings_btn = (
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
    row = []
    data = await sql.get_sub(chat_id)
    if data:
        mailing, notify, _ = data
        if notify:
            text = 'Выкл. уведомления'
        else:
            text = 'Вкл. уведомления'
        params = {'text': text, 'callback_data': 'settings-switch-notify'}
        row.append(params)
        if mailing:
            text = 'Выкл. рассылку'
        else:
            text = 'Вкл. рассылку'
        params = {'text': text, 'callback_data': 'settings-switch-mailing'}
        row.append(params)
    return (row,)


if __name__ == '__main__':
    import asyncio

    async def main():
        res = await get_notify_settings_btn(0)
        print(res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
