from src.lb import promise_available
from src.sql import sql
from src.bot.api.keyboards.kb_agrms import get_agrms_btn

payment_choice_btn = (
    (
        {'text': 'Оплата онлайн', 'callback_data': 'payments-online'},
        {'text': 'Обещанный платёж', 'callback_data': 'payments-promise'},
    ),
    (
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)


async def get_payment_agrms(chat_id):
    output = []
    agrms = await sql.get_agrms(chat_id)
    for agrm in agrms:
        agrm_id = await sql.get_agrm_id(chat_id, agrm)
        if await promise_available(agrm_id):
            output.append(agrm)
    return output


async def get_payment_btn(chat_id):
    agrms = await get_payment_agrms(chat_id)
    return await get_agrms_btn(agrms=agrms)


if __name__ == '__main__':
    import asyncio

    async def main():
        res = await get_payment_btn(0)
        print(res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
