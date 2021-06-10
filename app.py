__author__ = 'leichgardt'

import asyncio
import uvicorn
import uvloop
from fastapi import FastAPI, Request
from starlette.responses import Response, RedirectResponse
from fastapi_utils.tasks import repeat_every

from src.sql import sql
from src.utils import config, init_logger
from src.web import handle_payment_response, get_query_params, get_request_data, lan_require, telegram_api, \
    auto_payment_monitor, handle_new_payment_request, SoloWorker

loop = uvloop.new_event_loop()
logger = init_logger('irobot-web')
bot_name = ''
back_url = '<script>window.location = "tg://resolve?domain={}";</script>'
app = FastAPI(debug=False)
sw = SoloWorker(logger=logger)


@app.on_event('startup')
async def update_params():
    """Загрузить и обновить параметры"""
    global bot_name, back_url
    sql.pool_min_size = 2
    sql.pool_max_size = 5
    bot_name = await telegram_api.get_username()
    back_url = back_url.format(bot_name)
    logger.info(f'Bot API is available. "{bot_name}" are greetings you!')
    await sw.clean_old_pid_list()


@app.on_event('startup')
@repeat_every(seconds=50)
@sw.solo_worker(name='monitor')
async def payment_monitor():
    """
    Поиск незавершенных платежей.

    Чтобы завершить платёж, пользователь должен нажать на кнопку "Вернуться в магазин"  на странице оплаты.
    Если он этого не сделает, то эта функция автоматически найдет платёж в БД и в Биллинге, сопоставит
    их и уведомит абонента об успешной платеже."""
    await auto_payment_monitor(logger)


@app.on_event('shutdown')
async def close_connections():
    await sql.close_pool()
    await telegram_api.close()


@app.get('/')
@lan_require
async def hello(request: Request):
    return 'Hello, World'


@app.get('/new_payment')
async def new_yoomoney_payment(request: Request):
    """Перевести платёж в состояние "processing" для отслеживания монитором payment_monitor"""
    data = await get_request_data(request)
    if data and 'hash' in data:
        sql_data = await sql.find_payment(data['hash'])
        res = await handle_new_payment_request(data['hash'], sql_data)
        if res == 1:  # это новый платёж - перенаправить на страницу оплаты
            return RedirectResponse(sql_data[2], 302)
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
        if 'res' in data and data['res'] in ['success', 'fail']:
            hash_code = None
            if 'hash' in data:
                hash_code = data['hash']
            elif 'shopSuccessURL' in data or 'shopFailURL' in data:
                url = data.get('shopSuccessURL') or data.get('shopFailURL') or ''
                params = get_query_params(url)
                if 'hash' in params:
                    hash_code = params['hash'][0]
            if hash_code:
                await handle_payment_response(logger, data['res'], hash_code)
                return Response(back_url, 301)
            return RedirectResponse(config['yandex']['fallback-url'] + data['res'], 301)
    logger.warning(f'Bad payment request from {request.client.host}')
    return RedirectResponse(config['yandex']['fallback-url'] + 'fail', 301)


@app.post('/api_status')
async def api_status(request: Request):
    res = await sql.get_pid_list()
    if not res:
        return {'response': 0}
    res = await telegram_api.get_me()
    if not res:
        return {'response': 0}
    return {'response': 1}


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug, workers=4)
