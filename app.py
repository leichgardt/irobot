__author__ = 'leichgardt'

import asyncio
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response, RedirectResponse
from fastapi_utils.tasks import repeat_every

from src.sql import sql
from src.utils import config, init_logger
from src.web import handle_payment_response, get_query_params, get_request_data, lan_require, telegram_api, \
    auto_payment_monitor, handle_new_payment_request, SoloWorker, auto_feedback_monitor, Table, broadcast, login, \
    Context
from src.lb import check_account_pass
from guni import workers

VERSION = '0.3.1'
ABOUT = """Веб-приложение IroBot-web предназначено для рассылки новостей и уведомлений пользователям бота @ironnet_bot,
а так же для обработки запросов платежей от системы Yoomoney.
Сервис регистрирует новые платежи и мониторит их выполнение через систему LanBilling; и при обнаружении завершенного 
платежа сервис уведомляет пользователя через бота об успешной оплате."""

logger = init_logger('irobot-web', new_formatter=True)
sql.logger = logger
bot_name = ''
back_url = '<script>window.location = "tg://resolve?domain={}";</script>'
templates = Jinja2Templates(directory='templates')
app = FastAPI(debug=False, root_path='/irobot_web')
app.mount('/static', StaticFiles(directory='static', html=True), name='static')
sw = SoloWorker(logger=logger, workers=workers)


@app.on_event('startup')
async def update_params():
    """Загрузить и обновить параметры"""
    global bot_name, back_url
    sql.pool_min_size = 2
    sql.pool_max_size = 5
    bot_name = await telegram_api.get_me()
    bot_name = bot_name['username']
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


@app.on_event('shutdown')
async def close_connections():
    await sql.close_pool()
    await telegram_api.close()


@app.get('/')
@lan_require
async def index(request: Request):
    t_subs, t_history = '', ''
    res = await sql.get_sub_agrms()
    if res:
        data = {}
        for chat_id, agrm, mailing in res:
            if chat_id not in data:
                data.update({chat_id: {'agrms': str(agrm), 'mailing': mailing}})
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
                                      Context(request=request,
                                              title='IroBot',
                                              domain=config['paladin']['domain'],
                                              about=ABOUT,
                                              version=VERSION,
                                              tables={'subs': t_subs, 'history': t_history},
                                              ))


@app.get('/login')
async def login_page(request: Request):
    data = await get_request_data(request)
    context = Context(request=request,
                      title='Авторизация',
                      domain=config['paladin']['domain'],
                      bot_name=bot_name,
                      support_bot_name=config['irobot']['chatbot'],
                      )
    if data and 'hash' in data and await sql.find_chat_by_hash(data['hash']):
        return templates.TemplateResponse('login.html', context(hash_code=data['hash']))
    return templates.TemplateResponse('login_error.html', context)


@app.post('/api/login')
async def login_try(request: Request, response: Response, background_tasks: BackgroundTasks):
    data = await get_request_data(request)
    res, agrm_id = await check_account_pass(data['agrm'], data['pwd'])
    if res == 1:
        chat_id = await sql.find_chat_by_hash(data['hash'])
        if chat_id:
            if data['agrm'] in await sql.get_agrms(chat_id):
                logger.info(f'Agrm already added [{chat_id}]')
                return {'response': 2}
            logger.info(f'Logging [{chat_id}]')
            background_tasks.add_task(login, chat_id, data['agrm'], agrm_id)
            response.status_code = 202
            return {'response': 1}
        else:
            logger.info(f'Login: chat_id not found [{chat_id}]')
            return {'response': -1}
    elif res == 0:
        logger.info('Login: incorrect agrm or pwd [{}]'.format(data['agrm']))
        return {'response': 0}
    else:
        logger.info('Login error [{}]'.format(data['agrm']))
        return {'response': -1}


@app.get('/login_success')
async def login_page(request: Request):
    data = await get_request_data(request)
    context = Context(request=request,
                      title='Авторизация',
                      domain=config['paladin']['domain'],
                      bot_name=bot_name)
    if data and 'hash' in data and await sql.find_chat_by_hash(data['hash']):
        return templates.TemplateResponse('login_success.html', context)
    return templates.TemplateResponse('login_error.html', context)


@app.get('/api/get_history')
@lan_require
async def history(request: Request):
    """Получить таблицу с последними 10 рассылками"""
    res = await sql.get_mailings()
    if res:
        table = Table(res)
        return {'response': 1, 'table': table.get_html()}
    return {'response': 0}


@app.post('/api/send_mail')
@lan_require
async def send_mailing(request: Request, response: Response, background_tasks: BackgroundTasks):
    """Добавить новую рассылку"""
    data = await get_request_data(request)
    if data['mail_type'] in ('notify', 'mailing'):
        res = await sql.add_mailing(data['mail_type'], data['text'])
        if res:
            background_tasks.add_task(broadcast, logger)
            logger.info(f'New mailing added [{res[0][0]}]')
            response.status_code = 202
            return {'response': 1, 'id': res[0][0]}
        else:
            response.status_code = 500
            logger.error(f'Error of New mailing. Data: {data}')
            return {'response': -1, 'error': 'backand error'}
    else:
        response.status_code = 400
        return {'response': 0, 'error': 'wrong mail_type'}


@app.get('/api/new_payment')
async def new_yoomoney_payment(request: Request):
    """Перевести платёж в состояние "processing" для отслеживания монитором payment_monitor"""
    data = await get_request_data(request)
    if data and 'hash' in data:
        sql_data = await sql.find_payment(data['hash'])
        res = await handle_new_payment_request(data['hash'], sql_data)
        if res == 1:  # это новый платёж - перенаправить на страницу оплаты
            return RedirectResponse(sql_data[2], 302)
        elif res == 0:  # это старый платёж - вернуться к телеграм боту
            await asyncio.sleep(0.8)
            return Response(back_url, 301)
        else:  # непредвиденная ошибка
            return Response('Backend error', 500)
    return Response('Hash code not found', 400)


@app.get('/api/payment')
@app.post('/api/payment')
async def get_yoomoney_payment(request: Request):
    """
    Обработчик ответов от yoomoney

    В платеже есть параметры shopSuccessURL и shopFailURL.
    В зависимости от ответа меняется текст ответа пользователю и запись в БД.
    """
    data = await get_request_data(request)
    if data:
        if 'res' in data and data['res'] in ['success', 'fail']:
            hash_code = None
            if 'hash' in data:
                hash_code = data['hash']
            elif 'shopSuccessURL' in data or 'shopFailURL' in data:
                url = data.get('shopSuccessURL') or data.get('shopFailURL') or ''
                params = get_query_params(url)
                if 'hash' in params:
                    hash_code = params['hash'][0]
            if hash_code:
                await handle_payment_response(logger, data['res'], hash_code)
                return Response(back_url, 301)
            return RedirectResponse(config['yandex']['fallback-url'] + data['res'], 301)
    logger.warning(f'Bad payment request from {request.client.host}')
    return RedirectResponse(config['yandex']['fallback-url'] + 'fail', 301)


@app.post('/api/status')
async def api_status(request: Request):
    try:
        res1 = await sql.get_sub(config['irobot']['me'])
        res2 = await telegram_api.get_me()
    except Exception as e:
        logger.warning(e)
        return {'response': 0}
    else:
        if not res1 or not res2:
            return {'response': 0}
        return {'response': 1}


if __name__ == "__main__":
    app.debug = False
    uvicorn.run('app:app', host="0.0.0.0", port=8000, reload=app.debug, workers=4)
