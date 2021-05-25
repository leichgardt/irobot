back_to_main = (
    (
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)
main_menu_btn = (
    (
        {'text': ':scales: Баланс', 'callback_data': 'balance'},
        {'text': ':moneybag: Платежи', 'callback_data': 'payments'},
    ),
    (
        # {'text': 'Тариф', 'callback_data': 'tariff'},
        {'text': ':helmet_with_white_cross: Помощь', 'callback_data': 'help'},
        {'text': ':wrench: Настройки', 'callback_data': 'settings'},
    ),
    (
        # {'text': 'Помощь', 'callback_data': 'help'},
        {'text': '💩 Оставить отзыв', 'callback_data': 'review'},
    ),
)
help_btn = (
    (
        {'text': 'Обратиться в тех.поддержку', 'callback_data': 'support'},
    ),
    (
        {'text': 'Что я умею (youtube)', 'url': 'https://www.youtube.com/watch?v=bxqLsrlakK8'},
    ),
    (
        {'text': 'О программе', 'callback_data': 'about'},
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)
review_btn = (
    (
        {'text': 'Отправить', 'callback_data': 'send-review'},
        {'text': 'Отмена', 'callback_data': 'cancel'},
    ),
)


def get_review_btn(rating=0):
    smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
    btn = ([{'text': smile, 'callback_data': f'review-{i + 1}'} for i, smile in enumerate(smiles)],)
    if rating:
        btn[0][rating - 1]['text'] = '>{}<'.format(btn[0][rating - 1]['text'])
    return btn
