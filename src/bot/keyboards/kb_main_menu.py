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
        # {'text': 'Обратиться в тех.поддержку', 'url': 'tg://resolve?domain={}'},
    ),
    (
        {'text': 'О нас', 'callback_data': 'about'},
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)
review_btn = (
    (
        {'text': 'Отправить', 'callback_data': 'send-review'},
        {'text': 'Отмена', 'callback_data': 'cancel'},
    ),
)


def __update():
    from src.utils import config
    global help_btn
    help_btn[0][0]['url'] = help_btn[0][0]['url'].format(config['irobot']['chatbot'])


# __update()


def get_review_btn(rating=0, prefix_data='review'):
    smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
    btn = ([{'text': smile, 'callback_data': f'{prefix_data}-{i + 1}'} for i, smile in enumerate(smiles)],)
    if rating:
        btn[0][rating - 1]['text'] = '>{}<'.format(btn[0][rating - 1]['text'])
    return btn
