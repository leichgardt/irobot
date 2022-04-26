__author__ = 'leichgardt'

import asyncio

import uvloop
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from src.web.gunicorn_config import workers
from config import ABOUT, DEBUG, ROOT_PATH, SUPPORT_BOT  # ABOUT не удалять
from src.web.routers import api
from src.web.routers.admin import admin_router
from src.web.routers.user import login
from src.modules import lb, sql, Texts
from src.modules.sql.checker import CheckerSQL
from src.utils import aio_logger
from src.web import (
    SoloWorker,
    telegram_api,
    GlobalDict,
    chat_photo_update_monitor,
    auto_payment_monitor,
    auto_feedback_monitor,
    new_messages_monitor
)


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

app = FastAPI(root_path=ROOT_PATH if not DEBUG else None)
app.mount('/static', StaticFiles(directory='static', html=False), name='static')
app.include_router(api.router)
app.include_router(admin_router.router)
app.include_router(login.router)

templates = Jinja2Templates(directory='templates')

logger = aio_logger('irobot-web')
sql.logger = logger
lb.logger = logger
api.router.logger = logger
admin_router.router.logger = logger
login.router.logger = logger
sw = SoloWorker(logger=logger, workers=workers)

default_context = GlobalDict('web-default-context')
default_context['support_bot_name'] = SUPPORT_BOT

default_params = GlobalDict('web-default-parameters')
default_params['headers'] = {'Cache-Control': 'max-age=86400, must-revalidate'}

BOT_NAME = ''
BACK_TO_BOT_URL = '<script>window.location = "tg://resolve?domain={}";</script>'
BACK_LINK = '<a href="https://t.me/{bot_name}">Вернуться к боту @{bot_name}</a>'


@app.on_event('startup')
async def update_params():
    """ Загрузить и обновить параметры """
    global BOT_NAME, BACK_TO_BOT_URL, BACK_LINK, ABOUT

    # задать размер пула sql соединений
    sql.pool_min_size = 2
    sql.pool_max_size = 5

    # проверить и создать БД, если её нет
    sql_checker = CheckerSQL(sql)
    await sql_checker.check_db_ready()

    # загрузить данные бота и вставить их в переменные имён
    BOT_NAME = await telegram_api.get_me()
    BOT_NAME = BOT_NAME['username']
    Texts.web.login_try_again = [
        Texts.web.login_try_again[0].format(bot_name=BOT_NAME, support=SUPPORT_BOT)
    ]
    ABOUT = ABOUT.format(BOT_NAME)
    BACK_TO_BOT_URL = BACK_TO_BOT_URL.format(BOT_NAME)
    BACK_LINK = BACK_LINK.format(bot_name=BOT_NAME)
    default_context.update({'back_link': BACK_LINK})

    await sw.clean_old_pid_list()
    await logger.info(f'Irobot Web App [{sw.pid}] started. Hello there!')


@app.on_event('startup')
@repeat_every(seconds=60 * 60)
@sw.solo_worker(task='photo-updater', disabled=DEBUG)
async def photo_updater():
    await chat_photo_update_monitor()


@app.on_event('startup')
@repeat_every(seconds=1, wait_first=True)
@sw.solo_worker(task='support-messages')
async def messages_monitor():
    await new_messages_monitor(logger, admin_router.router.manager)


@app.on_event('startup')
@repeat_every(seconds=30)
@sw.solo_worker(task='payment-checker', disabled=DEBUG)
async def payment_monitor():
    """ Поиск платежей с ошибками и попытка провести платёж еще раз """
    await auto_payment_monitor(logger)


@app.on_event('startup')
@repeat_every(seconds=60)
@sw.solo_worker(task='feedback-userside', disabled=DEBUG)
async def feedback_monitor():
    """
    Поиск новых feedback сообщений для рассылки.
    Ответ абонента записывается в БД "irobot.feedback", задание которого комментируется в Userside через Cardinalis
    """
    await auto_feedback_monitor(logger)


@app.on_event('shutdown')
async def close_connections():
    await sw.close_tasks()
    await sql.close_pool()
    await telegram_api.close()
    await logger.shutdown()


@app.get('/')
async def index_page(request: Request):
    text = [
        'С нашим телеграм ботом ты сможешь пополнять баланс, подключать обещанный платеж, получать уведомления о '
        'заканчивающимся балансе и о работах на сети.',
        'Переходи по ссылке ниже, чтобы начать'
    ]
    message = {'title': 'Добро пожаловать!', 'textlines': text}
    context = dict(request=request, title='IroBot', message=message, **default_context)
    return templates.TemplateResponse('user/page.html', context, headers=default_params['headers'])
