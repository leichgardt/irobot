__author__ = 'leichgardt'

import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from starlette.responses import Response
from pydantic import BaseModel

from src.sql import sql
from src.utils import config, init_logger
from src.web import (
    lan_require,
    SoloWorker, Table,
    telegram_api, broadcast, logining,
    auto_payment_monitor, auto_feedback_monitor, rates_feedback_monitor)
from src.lb import lb
from guni import workers

VERSION = '1.0.0'
ABOUT = """Веб-приложение IroBot-web предназначено для рассылки новостей и уведомлений пользователям бота @{},
а так же для обработки запросов платежей от системы Yoomoney.
Сервис регистрирует новые платежи и мониторит их выполнение через систему LanBilling; и при обнаружении завершенного 
платежа сервис уведомляет пользователя через бота об успешной оплате."""

bot_name = ''
back_url = '<script>window.location = "tg://resolve?domain={}";</script>'
cache_header = {'Cache-Control': 'max-age=86400, must-revalidate'}

logger = init_logger('irobot-web', new_formatter=True)
sql.logger = logger
lb.logger = logger
templates = Jinja2Templates(directory='templates')
app = FastAPI(debug=False, root_path='/irobot')
app.mount('/static', StaticFiles(directory='static', html=False), name='static')
sw = SoloWorker(logger=logger, workers=workers)


@app.on_event('startup')
async def update_params():
    """Загрузить и обновить параметры"""
    global bot_name, back_url, ABOUT
    sql.pool_min_size = 2
    sql.pool_max_size = 5
    bot_name = await telegram_api.get_me()
    bot_name = bot_name['username']
    ABOUT = ABOUT.format(bot_name)
    back_url = back_url.format(bot_name)
    logger.info(f'Bot API is available. "{bot_name}" are greetings you!')
    await sw.clean_old_pid_list()


@app.on_event('startup')
@repeat_every(seconds=30)
@sw.solo_worker(task='monitor')
async def payment_monitor():
    """
    Поиск незавершенных платежей.

    Чтобы завершить платёж, пользователь должен нажать на кнопку "Вернуться в магазин"  на странице оплаты.
    Если он этого не сделает, то эта функция автоматически найдет платёж в БД и в Биллинге, сопоставит
    их и уведомит абонента об успешной платеже."""
    await auto_payment_monitor(logger)


@app.on_event('startup')
@repeat_every(seconds=60)
@sw.solo_worker(task='feedback')
async def feedback_monitor():
    """
    Поиск новых feedback сообщений для рассылки.
    Ответ абонента записывается в БД "irobot.feedback", задание которого комментируется в Userside через Cardinalis
    """
    await auto_feedback_monitor(logger)


@app.on_event('startup')
@repeat_every(seconds=600)
@sw.solo_worker(task='feedback-rates')
async def feedback_monitor():
    """
    Поиск новых feedback сообщений для рассылки.
    Ответ абонента записывается в БД "irobot.feedback", задание которого комментируется в Userside через Cardinalis
    """
    await rates_feedback_monitor(logger)


@app.on_event('shutdown')
async def close_connections():
    await sql.close_pool()
    await telegram_api.close()
    await sw.close_tasks()


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
    return templates.TemplateResponse('index.html',
                                      headers=cache_header,
                                      context=dict(request=request,
                                                   title='IroBot',
                                                   domain=config['paladin']['domain'],
                                                   about=ABOUT,
                                                   version=VERSION,
                                                   tables={'subs': t_subs, 'history': t_history},
                                                   ))


@app.get('/login')
async def login_page(request: Request, hash: str = None):
    context = dict(request=request,
                   title='Авторизация',
                   domain=config['paladin']['domain'],
                   bot_name=bot_name,
                   support_bot_name=config['irobot']['chatbot'],
                   )
    if hash and await sql.find_chat_by_hash(hash):
        context.update(dict(hash_code=hash))
        return templates.TemplateResponse('login.html', context, headers=cache_header)
    return templates.TemplateResponse('login_error.html', context, headers=cache_header)


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
                    logger.info(f'Login: account already added [{chat_id}]')
                    return {'response': 2}
                logger.info(f'Logining [{chat_id}]')
                background_tasks.add_task(logining, chat_id, item.login)
                response.status_code = 202
                return {'response': 1}
            else:
                logger.info(f'Login: chat_id not found [{item.login}]')
                return {'response': -1}
        elif res == 0:
            logger.info(f'Login: incorrect login or pwd [{item.login}]')
            return {'response': 0}
        else:
            logger.info(f'Login: error [{item.login}]')
            return {'response': -1}
    return {'response': -2}


@app.get('/login_success')
async def login_page(request: Request):
    return templates.TemplateResponse('login_success.html',
                                      dict(request=request,
                                           title='Авторизация',
                                           domain=config['paladin']['domain'],
                                           bot_name=bot_name),
                                      headers=cache_header)


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
        res = await sql.add_mailing(item.type, item.text)
        if res:
            background_tasks.add_task(broadcast, logger)
            logger.info(f'New mailing added [{res[0][0]}]')
            response.status_code = 202
            return {'response': 1, 'id': res[0][0]}
        else:
            response.status_code = 500
            logger.error(f'Error of New mailing. Data: {item}')
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
        logger.error(e)
    else:
        output -= 1 if not res1 else 0
        output -= 2 if not res2 else 0
    return {'response': output}


if __name__ == "__main__":
    app.debug = False
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug, workers=4)
