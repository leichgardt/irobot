__author__ = 'leichgardt'

import os
import sys
import uvicorn

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from starlette.responses import Response, RedirectResponse
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../'))

from src.bot.api import main_menu
from src.guni import workers
from src.lb import lb
from src.payments import yoomoney_pay
from src.sql import sql
from src.text import Texts
from src.utils import config, aio_logger
from src.web import (
    lan_require, get_request_data,
    SoloWorker, Table, WebM,
    telegram_api, broadcast, logining, send_message,
    auto_payment_monitor, auto_feedback_monitor, rates_feedback_monitor
)

VERSION = '1.0.2'
ABOUT = """Веб-приложение IroBot-web предназначено для рассылки новостей и уведомлений пользователям бота @{},
а так же для обработки запросов платежей от системы Yoomoney.
Сервис регистрирует новые платежи и мониторит их выполнение через систему LanBilling; и при обнаружении завершенного 
платежа сервис уведомляет пользователя через бота об успешной оплате."""

bot_name = ''
back_url = '<script>window.location = "tg://resolve?domain={}";</script>'
back_link = '<a href="https://t.me/{bot_name}">Вернуться к боту @{bot_name}</a>'
cache_header = {'Cache-Control': 'max-age=86400, must-revalidate'}

webm = WebM()
logger = aio_logger('irobot-web')
sql.logger = logger
lb.logger = logger
templates = Jinja2Templates(directory='templates')
app = FastAPI(debug=False, root_path='/irobot')
# app = FastAPI(debug=False, root_path='')
app.add_middleware(HTTPSRedirectMiddleware)
app.mount('/static', StaticFiles(directory='static', html=False), name='static')
sw = SoloWorker(logger=logger, workers=workers)


@app.on_event('startup')
async def update_params():
    """ Загрузить и обновить параметры """
    global bot_name, back_url, back_link, webm, ABOUT
    sql.pool_min_size = 2
    sql.pool_max_size = 5
    bot_name = await telegram_api.get_me()
    bot_name = bot_name['username']
    Texts.web.login_try_again = [
        Texts.web.login_try_again[0].format(bot_name=bot_name, support=config["irobot"]["chatbot"])]
    ABOUT = ABOUT.format(bot_name)
    back_url = back_url.format(bot_name)
    back_link = back_link.format(bot_name=bot_name)
    webm.update(back_link, bot_name, cache_header, templates)
    await sw.clean_old_pid_list()
    await logger.info(f'Irobot Web App [{sw.pid}] started. Hello there!')


@app.on_event('startup')
@repeat_every(seconds=30)
@sw.solo_worker(task='monitor')
async def payment_monitor():
    """ Поиск платежей с ошибками и попытка провести платёж еще раз """
    await auto_payment_monitor(logger)
    # await logger.info('monitor')


@app.on_event('startup')
@repeat_every(seconds=60)
@sw.solo_worker(task='feedback')
async def feedback_monitor():
    """
    Поиск новых feedback сообщений для рассылки.
    Ответ абонента записывается в БД "irobot.feedback", задание которого комментируется в Userside через Cardinalis
    """
    await auto_feedback_monitor(logger)
    # await logger.info('feedback')


@app.on_event('startup')
@repeat_every(seconds=600)
@sw.solo_worker(task='feedback-rates')
async def feedback_monitor():
    """
    Поиск новых feedback сообщений для рассылки.
    Ответ абонента записывается в БД "irobot.feedback", задание которого комментируется в Userside через Cardinalis
    """
    await rates_feedback_monitor(logger)
    # await logger.info('feedback-rates')


@app.on_event('shutdown')
async def close_connections():
    await sql.close_pool()
    await telegram_api.close()
    await sw.close_tasks()
    await logger.shutdown()


@app.get('/')
@lan_require
async def index(request: Request):
    t_subs, t_history = '', ''
    res = await sql.get_sub_agrms()
    if res:
        data = {}
        for chat_id, agrm, mailing in res:
            if chat_id not in data:
                data[chat_id] = {'agrms': str(agrm), 'mailing': mailing}
            else:
                data[chat_id]['agrms'] = data[chat_id]['agrms'] + '<br/>' + str(agrm)
        res = []
        for key, value in data.items():
            res.append([key, value['mailing'], value['agrms']])
        t_subs = Table(res)
        for line in t_subs:
            if not line[1].value:
                line[1].style = 'background-color: red;'
            else:
                line[1].style = 'background-color: green; color: white;'
        t_subs = t_subs.get_html()
    res = await sql.get_mailings()
    if res:
        t_history = Table(res).get_html()
    context = dict(title='IroBot', about=ABOUT, version=VERSION, tables={'subs': t_subs, 'history': t_history})
    return webm.page(request, context, template='index.html')


@app.get('/login')
async def login_page(request: Request, hash: str = None):
    if hash and await sql.find_chat_by_hash(hash):
        return webm.page(request, dict(title=Texts.web.auth, hash_code=hash), template='login.html')
    return webm.page(request, dict(title=Texts.web.auth, message=dict(
        title=Texts.web.error,
        textlines=Texts.web.login_try_again
    )))


class LoginItem(BaseModel):
    login: str = ''
    pwd: str = ''
    hash: str = ''


@app.post('/api/login')
async def login_try(response: Response,
                    background_tasks: BackgroundTasks,
                    item: LoginItem):
    """
    response: 1  - успешная авторизация
    response: 2  - договор уже добавлен к учётной записи
    response: 0  - неверный пароль
    response: -1 - договор не найден
    response: -2 - не переданы данные (agrm/password/hash)
    """
    if item.login and item.pwd and item.hash:
        res = await lb.check_account_pass(item.login, item.pwd)
        if res == 1:
            chat_id = await sql.find_chat_by_hash(item.hash)
            if chat_id:
                if item.login in await sql.get_accounts(chat_id):
                    await logger.info(f'Login: account already added [{chat_id}]')
                    return {'response': 2}
                await logger.info(f'Logining [{chat_id}]')
                background_tasks.add_task(logining, chat_id, item.login)
                response.status_code = 202
                return {'response': 1}
            else:
                await logger.info(f'Login: chat_id not found [{item.login}]')
                return {'response': -1}
        elif res == 0:
            await logger.info(f'Login: incorrect login or pwd [{item.login}]')
            return {'response': 0}
        else:
            await logger.info(f'Login: error [{item.login}]')
            return {'response': -1}
    return {'response': -2}


@app.get('/login_success')
async def login_page(request: Request):
    return webm.page(request, dict(title=Texts.web.auth, message=dict(title=Texts.web.auth_success)))


@app.get('/api/get_history')
@lan_require
async def history(request: Request):
    """Получить таблицу с последними 10 рассылками"""
    res = await sql.get_mailings()
    if res:
        table = Table(res)
        return {'response': 1, 'table': table.get_html()}
    return {'response': 0}


class MailingItem(BaseModel):
    type: str = ''
    text: str = ''


@app.post('/api/send_mail')
@lan_require
async def send_mailing(request: Request,
                       response: Response,
                       background_tasks: BackgroundTasks,
                       item: MailingItem):
    """Добавить новую рассылку"""
    if item.type in ('notify', 'mailing'):
        mail_id = await sql.add_mailing(item.type, item.text)
        if mail_id:
            background_tasks.add_task(broadcast, logger)
            await logger.info(f'New mailing added [{mail_id}]')
            response.status_code = 202
            return {'response': 1, 'id': mail_id}
        else:
            response.status_code = 500
            await logger.error(f'Error of New mailing. Data: {item}')
            return {'response': -1, 'error': 'backand error'}
    else:
        response.status_code = 400
        return {'response': 0, 'error': 'wrong mail_type'}


@app.post('/api/status')
@lan_require
async def api_status(request: Request):
    """
    response: 1  - OK
    response: 0  - SQL error
    response: -1 - telegram API error
    response: -2 - SQL and API error
    """
    output = 1
    try:
        res1 = await sql.get_sub(config['irobot']['me'])
        res2 = await telegram_api.get_me()
    except Exception as e:
        await logger.error(e)
    else:
        output -= 1 if not res1 else 0
        output -= 2 if not res2 else 0
    return {'response': output}


@app.get('/new_payment')
async def new_payment(request: Request, hash_code: str = None):
    url = 'payment?status=error'
    if hash_code:
        payment = await sql.find_payment(hash_code)
        if payment:
            if not payment['url'] and payment['status'] == 'new':
                yoo_payment = await yoomoney_pay(payment['agrm'], payment['amount'], hash_code)
                if yoo_payment:
                    url = yoo_payment['url']
                    await sql.upd_payment(hash_code, status='processing', url=yoo_payment['url'],
                                          receipt=yoo_payment['id'])
            elif payment['url']:
                url = payment['url']
    return RedirectResponse(url, 302)


@app.get('/payment')
async def get_payment(request: Request, hash_code: str = None):
    if hash_code:
        payment = await sql.find_payment(hash_code)
        if payment:
            if payment['status'] == 'processing':
                return webm.page(request, dict(title=Texts.web.payment_success, message=dict(
                    title=Texts.web.payment_processing,
                    message=Texts.web.payment_process_detail
                )))
            elif payment['status'] in ('success', 'finished'):
                return webm.page(request, dict(title=Texts.web.payment_success,
                                               message=dict(title=Texts.web.payment_success)))
            elif payment['status'] == 'error':
                return webm.page(request, dict(title=Texts.web.payment_error, message=dict(
                    title=Texts.web.payment_error,
                    textlines=Texts.web.payment_err_detail
                )))
    data = await get_request_data(request)
    await logger.info(f'Backend error [{request.client.host}]: {request.url}{f" {data}" if data else ""}')
    return webm.page(request, dict(message=dict(title=Texts.web.backend_error, textlines=Texts.web.backend_err_detail),
                                   title=Texts.web.error))


@app.post('/api/payment')
async def payment_processing(request: Request):
    data = await get_request_data(request)
    payment_id = 0
    if data and 'hash_code' in data and 'id' in data:
        payment = await sql.find_payment(data['hash_code'])
        if payment:
            payment_id = await lb.new_payment(payment['agrm'], payment['amount'], payment['receipt'])
            if payment_id:
                res = await send_message(payment['chat_id'], *Texts.payments_online_success.pair(),
                                         reply_markup=main_menu)
                await sql.upd_payment(data['hash_code'], status='finished' if res else 'success', receipt=data['id'],
                                      record_id=payment_id)
            else:
                await sql.upd_payment(data['hash_code'], status='error', receipt=data['id'])
    return {'response': payment_id}


if __name__ == "__main__":
    app.debug = False
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug, workers=4)
