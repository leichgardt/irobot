from src.bot.api.keyboard_button import KeyboardButton
from src.utils import config


__all__ = ['back_to_main', 'main_menu_btn', 'help_btn', 'review_btn', 'get_review_btn']


back_to_main = [
    KeyboardButton('Назад', callback_data='main-menu')
]

main_menu_btn = [
    [
        KeyboardButton(':scales: Баланс', callback_data='balance'),
        KeyboardButton(':moneybag: Платежи', callback_data='payments'),
    ],
    [
        # {'text': 'Тариф', 'callback_data': 'tariff'},
        KeyboardButton(':helmet_with_white_cross: Помощь', callback_data='help'),
        KeyboardButton(':wrench: Настройки', callback_data='settings'),
    ],
    [
        # {'text': 'Помощь', 'callback_data': 'help'},
        KeyboardButton('💩 Оставить отзыв', callback_data='review'),
    ],
]

help_btn = [
    [
        KeyboardButton('Обратиться в тех.поддержку', callback_data='support')
        # {'text': 'Обратиться в тех.поддержку', 'url': 'tg://resolve?domain={}'},
    ],
    [
        KeyboardButton('О нас', callback_data='about'),
        KeyboardButton('Назад', callback_data='main-menu')
     ],
]

review_btn = [
    KeyboardButton('Отправить', callback_data='send-review'),
    KeyboardButton('Отмена', callback_data='cancel'),
]


def get_review_btn(rating=0, prefix_data='review'):
    smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
    btn = [KeyboardButton(smile, callback_data=f'{prefix_data}-{i + 1}') for i, smile in enumerate(smiles)]
    if rating:
        btn[rating - 1]['text'] = '>{}<'.format(btn[rating - 1]['text'])
    return btn


def __update():
    global help_btn
    help_btn[0][0]['url'] = help_btn[0][0]['url'].format(config['irobot']['chatbot'])


# __update()
