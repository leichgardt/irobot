from src.bot.schemas.keyboard import KeyboardButton, Keyboard

__all__ = ('payment_choice_kb', 'back_to_payments_btn', 'get_payment_url_btn', 'payment_url_btn')


payment_choice_kb = Keyboard.inline([
    [
        KeyboardButton('Оплата онлайн', callback_data='payments-online'),
        KeyboardButton('Обещанный платёж', callback_data='payments-promise'),
    ],
    [
        KeyboardButton('Назад', callback_data='main-menu'),
    ],
])

back_to_payments_btn = [
    KeyboardButton('Назад', callback_data='payments')
]


def get_payment_url_btn(url, amount):
    return [
        [
            KeyboardButton(f'Заплатить {amount} RUB', url=url),
        ],
        [
            KeyboardButton('Изменить сумму', callback_data='payments-online-another-amount'),
            KeyboardButton('Отмена', callback_data='cancel'),
        ],
    ]


def payment_url_btn(url, amount):
    return [
        KeyboardButton(f'Оплатить {amount} RUB', url=url)
    ]
