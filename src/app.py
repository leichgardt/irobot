__author__ = 'leichgardt'

import uvicorn
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel

try:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent.resolve()))

    from src.guni import workers
    from src.lb import lb
    from src.parameters import SUPPORT_BOT, TEST_CHAT_ID
    from src.sql import sql
    from src.text import Texts
    from src.utils import aio_logger
    from src.web import (
        lan_require,
        get_request_data,
        SoloWorker,
        Table,
        WebM,
        telegram_api,
        broadcast,
        logining,
        send_message,
        send_feedback,
        auto_payment_monitor,
        auto_feedback_monitor,
        get_subscriber_table,
        get_mailing_history
    )
except ImportError as e:
    raise ImportError(f'{e}. Bad $PATH variable: {":".join(sys.path)}')


VERSION = '1.0.3a'
ABOUT = (
    'Веб-приложение IroBot-web предназначено для рассылки новостей и уведомлений пользователям бота @{}, '
    'а так же для обработки запросов платежей от системы Yoomoney.\n'
    'Сервис регистрирует новые платежи и мониторит их выполнение через систему LanBilling; и при обнаружении '
    'завершенного платежа сервис уведомляет пользователя через бота об успешной оплате.'
)
BOT_NAME = ''
BACK_TO_BOT_URL = '<script>window.location = "tg://resolve?domain={}";</script>'
BACK_LINK = '<a href="https://t.me/{bot_name}">Вернуться к боту @{bot_name}</a>'
HEADERS = {'Cache-Control': 'max-age=86400, must-revalidate'}
DATA_PACK = {'support_bot_name': SUPPORT_BOT}

logger = aio_logger('irobot-web')
sql.logger = logger
lb.logger = logger
templates = Jinja2Templates(directory='templates')
app = FastAPI(debug=False, root_path='/irobot')
app.add_middleware(HTTPSRedirectMiddleware)
app.mount('/static', StaticFiles(directory='static', html=False), name='static')
sw = SoloWorker(logger=logger, workers=workers)


@app.on_event('startup')
async def update_params():
    """ Загрузить и обновить параметры """
    global BOT_NAME, BACK_TO_BOT_URL, BACK_LINK, ABOUT
    # задать размер пула sql соединений
    sql.pool_min_size = 2
    sql.pool_max_size = 5

    # загрузить данные бота и вставить их в переменные имён
    BOT_NAME = await telegram_api.get_me()
    BOT_NAME = BOT_NAME['username']
    Texts.web.login_try_again = [
        Texts.web.login_try_again[0].format(bot_name=BOT_NAME, support=SUPPORT_BOT)
    ]
    ABOUT = ABOUT.format(BOT_NAME)
    BACK_TO_BOT_URL = BACK_TO_BOT_URL.format(BOT_NAME)
    BACK_LINK = BACK_LINK.format(bot_name=BOT_NAME)
    DATA_PACK.update({'back_link': BACK_LINK})

    await sw.clean_old_pid_list()
    await logger.info(f'Irobot Web App [{sw.pid}] started. Hello there!')


@app.on_event('startup')
@repeat_every(seconds=300)
@sw.solo_worker(task='payments')
async def payment_monitor():
    """ Поиск платежей с ошибками и попытка провести платёж еще раз """
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


@app.on_event('shutdown')
async def close_connections():
    await sql.close_pool()
    await telegram_api.close()
    await sw.close_tasks()
    await logger.shutdown()


@app.get('/')
@lan_require
async def index_page(request: Request):
    return templates.TemplateResponse('index.html', dict(title='IroBot', about=ABOUT, version=VERSION))


@app.get('/mailing')
@lan_require
async def mailing_page(request: Request):
    table = await get_subscriber_table() or ''
    history = await get_mailing_history() or ''
    context = dict(title='IroBot', about=ABOUT, version=VERSION, tables=dict(subs=table.get_html(), history=history))
    return templates.TemplateResponse('index.html', context)


@app.get('/login')
async def login_page(request: Request, hash_code: str = None):
    if hash_code and await sql.find_chat_by_hash(hash_code):
        context = dict(request=request, title=Texts.web.auth, hash_code=hash_code, **DATA_PACK)
        return templates.TemplateResponse('login.html', context, headers=HEADERS)
    message = {'title': Texts.web.error, 'textlines': Texts.web.login_try_again}
    context = dict(request=request, title=Texts.web.auth, message=message, **DATA_PACK)
    return templates.TemplateResponse('page.html', context, headers=HEADERS)


class LoginItem(BaseModel):
    login: str = ''
    pwd: str = ''
    hash: str = ''


@app.post('/api/login')
async def login_try_request(response: Response, background_tasks: BackgroundTasks, item: LoginItem):
    """
    Коды ответа:
         1 - успешная авторизация
         2 - договор уже добавлен к учётной записи
         0 - неверный пароль
        -1 - договор не найден
        -2 - не переданы данные (agrm/password/hash)
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
async def successful_login_page(request: Request):
    context = {'request': request, 'title': Texts.web.auth, 'message': {'title': Texts.web.auth_success}}
    return templates.TemplateResponse('page.html', context, headers=HEADERS)


@app.get('/api/get_history')
@lan_require
async def get_history_table_request(request: Request):  # НЕ УДАЛЯТЬ `request`! Требуется для декоратора `lan_require`
    """Получить таблицу с последними 10 рассылками"""
    res = await sql.get_mailings()
    if res:
        table = Table(res)
        for line in table:
            line[4].value = '\n'.join(line[4].value) if isinstance(line[4].value, list) else line[4].value
        return {'response': 1, 'table': table.get_html()}
    return {'response': 0}


class MailingItem(BaseModel):
    type: str = ''
    text: str = ''
    parse_mode: str = None


@app.post('/api/send_mail')
@lan_require
async def send_mailing_request(
        request: Request,  # НЕ УДАЛЯТЬ! Требуется для декоратора `lan_require`
        response: Response,
        background_tasks: BackgroundTasks,
        item: MailingItem
):
    """Добавить новую рассылку"""
    if item.type in ('notify', 'mailing'):
        mail_id = await sql.add_mailing(item.type, item.text)
        if mail_id:
            payload = dict(id=mail_id, type=item.type, text=item.text, parse_mode=item.parse_mode)
            background_tasks.add_task(broadcast, payload, logger)
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


@app.post('/api/send_message')
@lan_require
async def send_message_request(
        request: Request,
        response: Response,
        background_tasks: BackgroundTasks
):
    """
    Отправить сообщение
    если передан
        chat_id - сообщение напрямую в конкретный чат
        user_id - рассылка всем чатам (chat_id) пользователя (user_id)
        agrm_id - рассылка всем чатам (chat_id), у кого подключен договор (agrm_id)
        agrm    - тоже cамое, только по (agrm login), а не через (agrm_id)
    """
    data = await get_request_data(request)
    if data:
        chat_id = data.get('chat_id')
        user_id = data.get('user_id')
        agrm_id = data.get('agrm_id')
        agrm = data.get('agrm') or data.get('agrm_num')
        text = data.get('text')
        parse_mode = data.get('parse_mode')
        if text and (chat_id or user_id or agrm_id or agrm):
            targets = []
            mail_id = 0
            if chat_id:
                target_type = 'direct'
                targets = [chat_id]
                mail_id = await sql.add_mailing('direct', text, targets, parse_mode)
                msg = await send_message(chat_id, text, parse_mode=parse_mode)
                if msg:
                    await sql.upd_mailing_status(mail_id, 'complete')
                    return {'response': 1, 'id': mail_id}
            elif user_id:
                target_type = 'userid'
                if await sql.find_user_chats(user_id):
                    targets = [user_id]
                    mail_id = await sql.add_mailing(target_type, text, targets, parse_mode)
            elif agrm_id or agrm:
                target_type = 'direct'
                res = await lb.direct_request('getAccounts', {'agrmid': agrm_id} if agrm_id else {'agrmnum': agrm})
                targets = await sql.find_user_chats(res[0].account.uid)
                mail_id = await sql.add_mailing(target_type, text, targets, parse_mode)
            else:
                target_type = None
                targets = []
                mail_id = -1
            if mail_id > 0 and target_type:
                payload = dict(id=mail_id, type=target_type, targets=targets, text=text, parse_mode=parse_mode)
                background_tasks.add_task(broadcast, payload, logger)
                response.status_code = 202
                return {'response': 1, 'id': mail_id}
            elif mail_id == 0:
                response.status_code = 500
                return {'response': -1, 'error': 'Message registration error. Check the given data.'}
        response.status_code = 400
        return {'response': 0, 'error': f'Target not exist [{user_id or chat_id or agrm_id or agrm=}]'}
    response.status_code = 400
    return {'response': 0, 'error': 'Empty data'}


@app.post('/api/get_chat')
@lan_require
async def get_chat_request(request: Request, response: Response):
    """ Найти пользователя по фильтру """
    data = await get_request_data(request)
    agrm_num = data.get('agrm_num')
    agrm_id = data.get('agrm_id')
    login = data.get('login')
    user_id = data.get('user_id')
    if not (agrm_num or agrm_id or login or user_id):
        response.status_code = 400
        return {'response': 0, 'error': 'Data not provided'}
    if agrm_num:
        res = await lb.direct_request('getAccounts', {'agrmnum': agrm_num})
    elif agrm_id:
        res = await lb.direct_request('getAccounts', {'agrmid': agrm_id})
    elif login:
        res = await lb.direct_request('getAccounts', {'login': login})
    else:  # user_id
        res = await lb.direct_request('getAccounts', {'userid': user_id})
    if not res:
        response.status_code = 500
        return {'response': -1, 'error': 'User not found'}
    chats = await sql.find_user_chats(res[0].account.uid)
    if chats:
        return {'response': 1, 'result': chats}
    else:
        return {'response': -1, 'error': 'Chat not found'}


@app.post('/api/send_feedback')
@lan_require
async def send_feedback_request(request: Request, response: Response):
    """ Отправить пользователю feedback-сообщение """
    data = await get_request_data(request)
    task_id = data.get('task_id')
    login = data.get('login')
    if not (task_id and login):
        response.status_code = 400
        return {'response': 0, 'error': 'Task_id or agrm_num not specified'}
    acc = await lb.direct_request('getAccounts', {'login': login})
    if not acc:
        response.status_code = 500
        return {'response': -1, 'error': 'User by agreement number not found'}
    chats = await sql.find_user_chats(acc[0].account.uid)
    count = 0
    for chat_id in chats:
        msg = await send_feedback(chat_id, task_id)
        if msg and msg.message_id > 0:
            count += 1
    if not count:
        response.status_code = 500
        return {'response': -1, 'error': 'Messages not received'}
    return {'response': 1, 'messages': count}


@app.post('/api/status')
@lan_require
async def api_status(request: Request):  # для декоратора lan_require требуется аргумент `request`
    """
    response: 1  - OK
    response: 0  - SQL error
    response: -1 - telegram API error
    response: -2 - system fatal error
    """
    output = 1
    try:
        res1 = await sql.get_sub(TEST_CHAT_ID)
        res2 = await telegram_api.get_me()
    except Exception as e:
        await logger.error(e)
    else:
        output -= 1 if not res1 else 0
        output -= 2 if not res2 else 0
    return {'response': output}


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug, workers=4)
