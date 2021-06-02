__author__ = 'leichgardt'

import uvicorn
import uvloop
from fastapi import FastAPI, Request
from starlette.responses import Response, RedirectResponse
from functools import wraps
from urllib.parse import urlparse, parse_qs

from src.sql import sql
from src.utils import config, init_logger
from src.bot.text import BOT_NAME
from src.web import handle_payment_response

loop = uvloop.new_event_loop()
app = FastAPI(debug=False)
logger = init_logger('irobot-web')



def get_query_params(url):
    return parse_qs(urlparse(url).query)


async def get_request_data(request: Request):
    if request.method == 'GET':
        data = request.query_params
    else:
        try:
            data = await request.json()
        except:
            data = await request.form()
    return data if data else {}


def lan_require(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        ip = request.client.host
        if ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip[:8] == '192.168.' or \
                ip == config['paladin']['ironnet-global']:
            return await func(request, *args, **kwargs)
        else:
            logger.info(f'Access denied for {ip}')
            return Response(status_code=403)
    return wrapper


@app.get('/')
@lan_require
async def hello(request: Request):
    return 'Hello, World'


@app.get('/new_payment')
async def new_yoomoney_payment(request: Request):
    data = await get_request_data(request)
    if data and 'hash' in data:
        res = await sql.find_payment(data['hash'])
        if res:
            await sql.upd_payment(data['hash'], status='processing')
            return RedirectResponse(res[2], 302)
        return Response('Backend error', 500)
    return Response('Hash code not found', 400)


@app.get('/payment')
@app.post('/payment')
async def get_yoomoney_payment(request: Request):
    """
    Обработчик ответов от yoomoney
    В платеже есть параметры success-Url и fail-Url.
    Пример:
    https://market.net/payment?hash=###&res=success

    В зависимости от ответа меняется текст ответа пользователю и изменение записи в БД.
    """
    data = await get_request_data(request)
    if data:
        if 'res' in data:
            hash_code = None
            if 'shopSuccesURL' in data or 'shopFailURL' in data:
                url = data.get('shopSuccesURL') or data.get('shopFailURL') or ''
                params = get_query_params(url)
                if 'hash' in params:
                    hash_code = params['hash'][0]
            if hash_code:
                await handle_payment_response(data['res'], hash_code)
                html = '<script>window.location = "tg://resolve?domain={}";</script>'.format(BOT_NAME[1:])
                return Response(html, 308)
            else:
                return RedirectResponse(config['yandex']['fallback-url'] + data['res'])
    logger.warning(f'Payment bad request from {request.client.host}')
    return RedirectResponse(config['yandex']['fallback-url'] + 'fail')


@app.get('/payment/{path}')
@app.post('/payment/{path}')
async def get_yoomoney_payment_path(request: Request, path: str):
    data = await get_request_data(request)
    print('\n###### payment path ######')
    print('path:', path)
    print(request.method)
    print(data)
    return data


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug)
