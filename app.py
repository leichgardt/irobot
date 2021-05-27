from flask import Flask, request, redirect
from functools import wraps
from inspect import iscoroutinefunction
from pprint import pprint

from src.sql import SQLMaster
from src.utils import flogger as logger, config
from src.web import telegram_api, edit_message, delete_message
from src.bot.text import Texts
from src.bot.api import main_menu


app = Flask(__name__)
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
    if data and 'hash' in data and 'res' in data:
        payment_id, chat_id, _, status, _ = await sql.find_payment(data['hash'])
        if status == 'new':
            if data['res'] == 'success':
                text, parse, res = Texts.payments_online_success, Texts.payments_online_success.parse_mode, 'success'
            elif data['res'] == 'fail':
                text, parse, res = Texts.payments_online_fail, Texts.payments_online_fail.parse_mode, 'fail'
            else:
                logger.fatal(f'Payment error!!! Id: {payment_id}')
                text, parse, res = Texts.payment_error, Texts.payment_error.parse_mode, 'error'
            await sql.upd_payment_status(data['hash'], res)
        else:
            logger.error(f'Payment error! Already completed. Id: {payment_id}')
            text, parse = Texts.payment_error, Texts.payment_error.parse_mode
        await telegram_api.send_message(chat_id, text, parse, reply_markup=main_menu)
        return '<script>window.close();</script>', 200
    else:
        logger.warning('Payment bad request from yoomoney')
        return 'There is no form data', 400


@app.route('/payment/<path:path>', methods=['GET', 'POST'])
def get_yoomoney_payment_path(path):
    json_data = request.get_json()
    print('path:', path)
    print('payment path')
    print(request.method)
    pprint(json_data)
