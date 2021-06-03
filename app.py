__author__ = 'leichgardt'

import uvicorn
import uvloop
from fastapi import FastAPI, Request
from starlette.responses import Response, RedirectResponse
from fastapi_utils.tasks import repeat_every

from src.bot.api import main_menu
from src.bot.text import Texts
from src.sql import sql
from src.utils import config, init_logger
from src.web import handle_payment_response, get_query_params, get_request_data, lan_require, telegram_api, auto_payment_monitor

loop = uvloop.new_event_loop()
logger = init_logger('irobot-web')
bot_name = ''
back_url = '<script>window.location = "tg://resolve?domain={}";</script>'
app = FastAPI(debug=False)


@app.on_event('startup')
async def update_params():
    """Загрузить и обновить параметры"""
    global bot_name, back_url
    bot_name = await telegram_api.get_username()
    back_url = back_url.format(bot_name)
    logger.info(f'Bot API is available. "{bot_name}" greetings!')


@app.on_event('startup')
@repeat_every(seconds=50)
async def payment_monitor():
    """
    Поиск незавершенных платежей.

    Чтобы завершить платёж, пользователь должен нажать на кнопку "Вернуться в магазин", на странице оплаты.
    Если он этого не сделает, эта функция автоматически найдет платёж в БД и в Биллинге, сопоставит
    их и уведомит абонента об успешном платеже."""
    await auto_payment_monitor()


@app.get('/')
@lan_require
async def hello(request: Request):
    return 'Hello, World'


@app.get('/new_payment')
async def new_yoomoney_payment(request: Request):
    """Перевести платёж в состояние "processing" для отслеживания монитором payment_monitor"""
    data = await get_request_data(request)
    if data and 'hash' in data:
        res = await sql.find_payment(data['hash'])
        if res:
            if res[3] in ['new', 'processing']:
                if res[3] == 'new':
                    await sql.upd_payment(data['hash'], status='processing')
                return RedirectResponse(res[2], 302)
            else:
                await telegram_api.send_message(res[1], Texts.payment_error, Texts.payment_error.parse_mode,
                                                reply_markup=main_menu)
                return Response(back_url, 301)
        return Response('Backend error', 500)
    return Response('Hash code not found', 400)


@app.get('/payment')
@app.post('/payment')
async def get_yoomoney_payment(request: Request):
    """
    Обработчик ответов от yoomoney

    В платеже есть параметры shopSuccesURL и shopFailURL.
    В зависимости от ответа меняется текст ответа пользователю и запись в БД.
    """
    data = await get_request_data(request)
    if data:
        if 'res' in data:
            if 'shopSuccesURL' in data or 'shopFailURL' in data:
                url = data.get('shopSuccesURL') or data.get('shopFailURL') or ''
                params = get_query_params(url)
                if 'hash' in params:
                    await handle_payment_response(data['res'], params['hash'][0])
                    return Response(back_url, 301)
            return RedirectResponse(config['yandex']['fallback-url'] + data['res'], 301)
    logger.warning(f'Payment bad request from {request.client.host}')
    return RedirectResponse(config['yandex']['fallback-url'] + 'fail', 301)


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug)
