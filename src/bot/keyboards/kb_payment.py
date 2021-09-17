payment_choice_btn = (
    (
        {'text': 'Оплата онлайн', 'callback_data': 'payments-online'},
        {'text': 'Обещанный платёж', 'callback_data': 'payments-promise'},
    ),
    (
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)

back_to_payments_btn = (
    (
        {'text': 'Назад', 'callback_data': 'payments'},
    ),
)

# payment_btn = (
#     (
#         {'text': 'Изменить сумму', 'callback_data': 'payments-online-another-amount'},
#         {'text': 'Отменить платёж', 'callback_data': 'cancel'},
#     ),
# )


def get_payment_url_btn(url):
    return (
        (
            {'text': 'Оплатить', 'url': url},
        ),
        (
            {'text': 'Изменить сумму', 'callback_data': 'payments-online-another-amount'},
            {'text': 'Отмена', 'callback_data': 'cancel'},
        ),
    )