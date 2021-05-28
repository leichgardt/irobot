__author__ = 'leichgardt'

from flask import Flask, request, redirect, render_template
from functools import wraps
from inspect import iscoroutinefunction
from pprint import pprint

from src.sql import SQLMaster
from src.utils import flogger as logger, config
from src.web import handle_payment_response


app = Flask(__name__, static_folder='static')
app.logger = logger
sql = SQLMaster()


def lan_require(func):
    @wraps(func)
    async def awrapper(*args, **kwargs):
        ip = request.remote_addr
        if ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip[:8] == '192.168.' or \
                ip == config['paladin']['ironnet-global']:
            return await func(*args, **kwargs), 200
        else:
            logger.info(f'Access denied for {ip}')
            return '', 403

    @wraps(func)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr
        if ip == 'localhost' or ip[:8] == '192.168.' or ip == config['paladin']['ironnet-global']:
            return func(*args, **kwargs), 200
        else:
            return '', 403
    return awrapper if iscoroutinefunction(func) else wrapper


@app.route('/')
@lan_require
async def hello():
    return 'Hello, World'


@app.route('/new_payment', methods=['GET'])
async def new_yoomoney_payment():
    data = request.args
    if data:
        if 'hash' in data.keys():
            res = await sql.find_payment(data['hash'])
            if res[0]:
                return redirect(res[2])
    return 'Backend error', 500
    # return redirect('test')  # backend error page
    # return '<script>window.close();</script>', 200


@app.route('/payment', methods=['GET', 'POST'])
async def get_yoomoney_payment():
    """
    Обработчик ответов он yoomoney
    В платеже есть параметры success-Url и fail-Url.
    Пример:
    https://market.net/payment?hash=###&res=success

    В зависимости от ответа меняется текст ответа пользователю и изменение записи в БД.
    """
    if request.method == 'GET':
        data = request.args
    else:
        try:
            data = request.get_json()
        except:
            data = request.form
    if data and 'res' in data:
        if 'hash' in data:
            if not await handle_payment_response(sql, data['res'], data['hash']):
                return redirect(config['yandex']['fallback-url'] + data['res'])
        else:
            return redirect(config['yandex']['fallback-url'] + data['res'])
        return '<script>window.close();</script>', 200
    else:
        logger.warning(f'Payment bad request from {request.remote_addr}')
        return redirect(config['yandex']['fallback-url'] + 'fail')
        # return 'There is no form data', 400


@app.route('/payment/<path:path>', methods=['GET', 'POST'])
def get_yoomoney_payment_path(path):
    json_data = request.get_json()
    print('path:', path)
    print('payment path')
    print(request.method)
    pprint(json_data)
