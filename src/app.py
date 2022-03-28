__author__ = 'leichgardt'

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

try:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent.resolve()))

    from src.guni import workers
    from src.lb import lb
    from src.parameters import SUPPORT_BOT
    from src.routers import api, login
    from src.sql import sql
    from src.text import Texts
    from src.utils import aio_logger
    from src.web import (
        lan_require,
        SoloWorker,
        telegram_api,
        get_subscriber_table,
        get_mailing_history,
        GlobalDict,
    )
except ImportError as e:
    raise ImportError(f'{e}. Bad $PATH variable: {":".join(sys.path)}')
app = FastAPI(debug=True)


default_context = GlobalDict('web-default-context')
default_params = GlobalDict('web-default-parameters')

app = FastAPI(debug=False, root_path='/irobot')
app.add_middleware(HTTPSRedirectMiddleware)
app.mount('/static', StaticFiles(directory='static', html=False), name='static')
app.include_router(api.router)
app.include_router(login.router)

templates = Jinja2Templates(directory='templates')

logger = aio_logger('irobot-web')
sql.logger = logger
lb.logger = logger
api.router.logger = logger
login.router.logger = logger
sw = SoloWorker(logger=logger, workers=workers)


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
default_context['support_bot_name'] = SUPPORT_BOT
default_params['headers'] = {'Cache-Control': 'max-age=86400, must-revalidate'}


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
    default_context.update({'back_link': BACK_LINK})

    await sw.clean_old_pid_list()
    await logger.info(f'Irobot Web App [{sw.pid}] started. Hello there!')


@app.on_event('startup')
@repeat_every(seconds=30)
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


if __name__ == "__main__":
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug, workers=4)
