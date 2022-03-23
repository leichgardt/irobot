from src.bot.api.keyboard import KeyboardButton, Keyboard


__all__ = ('main_menu_kb', 'back_to_main', 'help_kb', 'review_btn', 'get_review_btn')

main_menu_kb = Keyboard([
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
        KeyboardButton('💩 Оставить отзыв', callback_data='review'),
    ],
]).reply(one_time_keyboard=True)

help_kb = Keyboard([
    [
        KeyboardButton('Обратиться в тех.поддержку', callback_data='support')
        # KeyboardButton('Обратиться в тех.поддержку', url='tg://resolve?domain={}'),
    ],
    [
        KeyboardButton('О нас', callback_data='about'),
        KeyboardButton('Назад', callback_data='main-menu')
     ],
]).inline()

back_to_main = [
    KeyboardButton('Назад', callback_data='main-menu')
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


# def __update():
#     global help_btn
#     help_btn[0][0]['url'] = help_btn[0][0]['url'].format(config['irobot']['chatbot'])
#
#
# __update()
