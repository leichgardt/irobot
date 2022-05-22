__author__ = 'leichgardt'

import asyncio

import uvloop
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

import config
from src.modules import lb, cache_server, sql, Texts
from src.modules.sql.checker import CheckerSQL
from src.web import tasks
from src.web.gunicorn_config import workers
from src.web.routers import api
from src.web.routers.admin import auth, chat, control_panel, mailing
from src.web.routers.user import login
from src.web.utils import solo_worker, telegram_api, global_dict, api as web_utils
from src.utils import AIOLogger


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

app = FastAPI(root_path=config.ROOT_PATH if not config.DEBUG else None)
app.mount('/static', StaticFiles(directory='static', html=False), name='static')

templates = Jinja2Templates(directory='templates')

logger = AIOLogger(name='irobot-web')
sql.logger = logger
lb.logger = logger

web_utils.add_routers_to_app(api, auth, chat, control_panel, mailing, login, app=app, logger=logger)

sw = solo_worker.SoloWorker(logger=logger, workers=workers)

default_context = global_dict.GlobalDict('web-default-context')
default_context['support_bot_name'] = config.SUPPORT_BOT

default_params = global_dict.GlobalDict('web-default-parameters')
default_params['headers'] = {'Cache-Control': 'max-age=86400, must-revalidate'}

BOT_NAME = ''
BACK_TO_BOT_URL = '<script>window.location = "tg://resolve?domain={}";</script>'
BACK_LINK = '<a href="https://t.me/{bot_name}">Вернуться к боту @{bot_name}</a>'


@app.on_event('startup')
async def update_params():
    """ Загрузить и обновить параметры """
    global BOT_NAME, BACK_TO_BOT_URL, BACK_LINK

    # подключится к серверу Redis
    cache_server.connect()

    # задать размер пула sql соединений
    sql.pool_min_size = 2
    sql.pool_max_size = 5

    # проверить и создать БД, если её нет
    sql_checker = CheckerSQL(sql)
    await sql_checker.check_db_ready()

    # загрузить данные бота и вставить их в переменные имён
    BOT_NAME = await telegram_api.telegram_api.get_me()
    BOT_NAME = BOT_NAME['username']
    Texts.web.login_try_again = [
        Texts.web.login_try_again[0].format(bot_name=BOT_NAME, support=config.SUPPORT_BOT)
    ]
    config.ABOUT = config.ABOUT.format(BOT_NAME)
    BACK_TO_BOT_URL = BACK_TO_BOT_URL.format(BOT_NAME)
    BACK_LINK = BACK_LINK.format(bot_name=BOT_NAME)
    default_context.update({'back_link': BACK_LINK})

    await sw.clean_old_pid_list()
    await logger.info(f'Irobot Web App [{sw.pid}] started. Hello there!')


@app.on_event('startup')
@repeat_every(seconds=60 * 60, wait_first=True)
@sw.solo_worker(task='photo-updater', disabled=config.DEBUG)
async def photo_updater():
    tasks.update_subscriber_chat_photos.apply_async()


@app.on_event('startup')
@repeat_every(seconds=1, wait_first=True)
@sw.solo_worker(task='support-messages', disabled=True)
async def messages_monitor():
    tasks.get_new_subscriber_messages_and_send_to_operators.apply_async(logger, chat.manager)


@app.on_event('startup')
@repeat_every(seconds=30)
@sw.solo_worker(task='payment-checker', disabled=config.DEBUG)
async def payment_monitor():
    """ Поиск платежей с ошибками и попытка провести платёж еще раз """
    tasks.handle_incomplete_bot_payments.apply_async(logger)


@app.on_event('startup')
@repeat_every(seconds=60)
@sw.solo_worker(task='feedback-userside', disabled=config.DEBUG)
async def feedback_monitor():
    """
    Поиск новых feedback сообщений для рассылки.
    Ответ абонента записывается в БД "irobot.feedback", задание которого комментируется в Userside через Cardinalis
    """
    tasks.handle_feedback_tasks.apply_async(logger)


@app.on_event('shutdown')
async def close_connections():
    await sw.wait_tasks()
    await telegram_api.telegram_api.close()
    await sql.close_pool()
    await logger.shutdown()
    await cache_server.close()


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
