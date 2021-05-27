from flask import Flask, request, redirect
from functools import wraps
from inspect import iscoroutinefunction
from pprint import pprint

from src.sql import SQLMaster
from src.utils import flogger as logger, config


app = Flask(__name__)
app.logger = logger
sql = SQLMaster()


def lan_require(func):
    @wraps(func)
    async def awrapper(*args, **kwargs):
        ip = request.remote_addr
        if ip == 'localhost' or ip[:8] == '192.168.' or ip == config['paladin']['ironnet-global']:
            return await func(*args, **kwargs), 200
        else:
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
            res = await sql.get_payment(data['hash'])
            if res:
                return redirect(res[1])
    return 'Backend error', 500
    # return redirect('test')  # backend error page
    # return '<script>window.close();</script>', 200


@app.route('/payment', methods=['GET', 'POST'])
def get_yoomoney_payment():
    if request.method == 'GET':
        data = request.args
        print('payment get')
    else:
        try:
            data = request.get_json()
            print('payment post json')
        except:
            data = request.form
            print('payment post form')
    if data:
        pprint(data)
        if data['res'] == 'success':
            pass
        elif data['res'] == 'fail':
            pass
        else:
            pass


@app.route('/payment/<path:path>', methods=['GET', 'POST'])
def get_yoomoney_payment_path(path):
    json_data = request.get_json()
    print('path:', path)
    print('payment path')
    print(request.method)
    pprint(json_data)
