__author__ = 'leichgardt'

import uvicorn
import uvloop
from fastapi import FastAPI, Request
from starlette.responses import Response, RedirectResponse
from datetime import datetime, timedelta
from fastapi_utils.tasks import repeat_every

from src.bot.text import Texts, BOT_NAME
from src.lb import get_payments
from src.sql import sql
from src.utils import config, init_logger
from src.web import handle_payment_response, get_query_params, get_request_data, lan_require, telegram_api

loop = uvloop.new_event_loop()
app = FastAPI(debug=False)
logger = init_logger('irobot-web')


@app.on_event('startup')
@repeat_every(seconds=50)
async def payment_monitor():
    """
    Поиск незавершенных платежей.

    Чтобы завершить платёж, пользователь должен нажать на кнопку "Вернуться в магазин", на странице оплаты.
    Если он этого не сделает, эта функция автоматически найдет платёж в БД и в Биллинге, сопоставит
    их и уведомит абонента об успешном платеже."""
    payments = await sql.find_processing_payments()
    if payments:
        logger.info('Auto-detector of new payments: found', len(payments))
        for pay_id, hash_code, chat_id, upd_date, agrm, amount, notified in payments:
            if datetime.now() - upd_date > timedelta(days=1):
                await sql.upd_payment(hash_code, status='canceled')
            else:
                agrm_id = await sql.get_agrm_id(chat_id, agrm)
                payments = await get_payments(agrm_id, minutes=230)
                for payment in payments:
                    if not await sql.find_payments_by_record_id(payment.pay.recordid):
                        koef = (float(payment.amountcurr) / float(amount)) - 1
                        if abs(koef) < 0.01:
                            text, parse = Texts.payments_online_success, Texts.payments_online_success.parse_mode
                            if not notified:
                                await telegram_api.send_message(chat_id, text, parse)
                                await sql.upd_payment(hash_code, status='finished', record_id=payment.pay.recordid,
                                                      notified=True)
                            else:
                                await sql.upd_payment(hash_code, status='finished', record_id=payment.pay.recordid)
                            logger.info(f'Payment finished [{pay_id}]')
                            break


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
