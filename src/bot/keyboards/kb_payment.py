payment_choice_btn = (
    (
        {'text': 'Оплата онлайн', 'callback_data': 'payments-online'},
        {'text': 'Обещанный платёж', 'callback_data': 'payments-promise'},
    ),
    (
        {'text': 'Назад', 'callback_data': 'cancel'},
    ),
)


def get_payment_url_btn(url):
    return (
        (
            {'text': 'Оплатить', 'url': url},
            {'text': 'Изменить сумму', 'callback_data': 'payments-online-another-amount'},
        ),
    )


async def get_promise_payment_agrms(chat_id=None, agrms=None):
    """договоры, доступные для обещанного платежа"""
    from src.lb import promise_available
    from src.sql import sql
    output = []
    if chat_id:
        agrms = await sql.get_agrms(chat_id)
    for agrm in agrms:
        agrm_id = await sql.get_agrm_id(chat_id, agrm)
        if await promise_available(agrm_id):
            output.append(agrm)
    return output


async def get_promise_payment_btn(chat_id=None, agrms=None):
    """кнопки с договорами для обещанного платежа"""
    from src.bot.keyboards.kb_agrms import get_agrms_btn
    if chat_id and not agrms:
        agrms = await get_promise_payment_agrms(chat_id)
    else:
        agrms = await get_promise_payment_agrms(chat_id, agrms)
    return await get_agrms_btn(agrms=agrms)
