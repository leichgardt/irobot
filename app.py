__author__ = 'leichgardt'

import asyncio
import uvicorn
import uvloop
from fastapi import FastAPI, Request
from starlette.responses import Response, RedirectResponse
from fastapi_utils.tasks import repeat_every

from src.utils import config, init_logger
from src.web import handle_payment_response, get_query_params, get_request_data, lan_require, telegram_api, \
    auto_payment_monitor, handle_new_payment_request

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
        res = await handle_new_payment_request(data['hash'])
        if res == 1:  # это новый платёж - перенаправить на страницу оплаты
            return RedirectResponse(res[2], 302)
        elif res == 0:  # это старый платёж - вернуться к телеграм боту
            await asyncio.sleep(0.8)
            return Response(back_url, 301)
        else:  # непредвиденная ошибка
            return Response('Backend error', 500)
    return Response('Hash code not found', 400)


@app.get('/payment')
@app.post('/payment')
async def get_yoomoney_payment(request: Request):
    """
    Обработчик ответов от yoomoney

    В платеже есть параметры shopSuccessURL и shopFailURL.
    В зависимости от ответа меняется текст ответа пользователю и запись в БД.
    """
    data = await get_request_data(request)
    if data:
        if 'res' in data:
            hash_code = None
            if 'hash' in data:
                hash_code = data['hash']
            elif 'shopSuccessURL' in data or 'shopFailURL' in data:
                url = data.get('shopSuccessURL') or data.get('shopFailURL') or ''
                params = get_query_params(url)
                if 'hash' in params:
                    hash_code = params['hash']
            if hash_code:
                await handle_payment_response(data['res'], params['hash'][0])
                await asyncio.sleep(0.5)
                return Response(back_url, 301)
            return RedirectResponse(config['yandex']['fallback-url'] + data['res'], 301)
    logger.warning(f'Payment bad request from {request.client.host}')
    return RedirectResponse(config['yandex']['fallback-url'] + 'fail', 301)


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug)
