payment_choice_btn = (
    (
        {'text': 'Оплата онлайн', 'callback_data': 'payments-online'},
        {'text': 'Обещанный платёж', 'callback_data': 'payments-promise'},
    ),
    (
        {'text': 'Назад', 'callback_data': 'cancel'},
    ),
)

payment_btn = (
    (
        {'text': 'Изменить сумму', 'callback_data': 'payments-online-another-amount'},
        {'text': 'Отменить платёж', 'callback_data': 'cancel'},
    ),
)
