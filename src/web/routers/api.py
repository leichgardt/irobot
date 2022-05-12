from fastapi import Request, Response, BackgroundTasks
from fastapi.templating import Jinja2Templates

from config import TELEGRAM_TEST_CHAT_ID
from src.modules import lb, sql
from src.web.schemas.router import MyAPIRouter
from src.web.utils import mailing as mailing_utils
from src.web.utils.api import lan_require, get_request_data
from src.web.utils.telegram_api import telegram_api, send_feedback

router = MyAPIRouter(prefix='/api')
templates = Jinja2Templates(directory='templates')


@router.post('/send_message')
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
        agrm    - тоже самое, только по (agrm login), а не через (agrm_id)
    """
    data = await get_request_data(request)
    if data:
        chat_id = data.get('chat_id')
        user_id = data.get('uid', data.get('userid', data.get('user_id')))
        agrm_id = data.get('aid', data.get('agrmid', data.get('agrm_id')))
        agrm = data.get('agrm', data.get('agrmnum', data.get('agrm_num')))
        text = data.get('text')
        parse_mode = data.get('parse_mode')
        if text and (user_id or chat_id or agrm_id or agrm):
            if user_id:
                target_type = 'user_id'
            elif chat_id:
                target_type = 'chat_id'
            elif agrm_id:
                target_type = 'agrm_id'
            else:
                target_type = 'agrm'
            mail_id, targets = await mailing_utils.distribute_message(
                text,
                parse_mode,
                target_type,
                user_id or chat_id or agrm_id or agrm
            )
            if mail_id > 0:
                payload = dict(id=mail_id, type='direct', targets=targets, text=text, parse_mode=parse_mode)
                background_tasks.add_task(mailing_utils.broadcast, payload, router.logger)
                response.status_code = 202
                return {'response': 1}
            else:
                response.status_code = 500
                return {'response': 0, 'error': 'Message registration error. Check the given data'}
    response.status_code = 400
    return {'response': 0, 'error': 'Empty data'}


@router.post('/get_chat')
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


@router.post('/send_feedback')
@lan_require
async def send_feedback_request(request: Request, response: Response):
    """ Отправить пользователю feedback-сообщение для Userside """
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


@router.post('/status')
@lan_require
async def api_status(_: Request):
    """
    response: 1  - OK
    response: 0  - SQL error
    response: -1 - telegram API error
    response: -2 - system fatal error
    """
    output = 1
    try:
        res1 = await sql.get_sub(TELEGRAM_TEST_CHAT_ID)
        res2 = await telegram_api.get_me()
    except Exception as e:
        await router.logger.error(e)
    else:
        output -= 1 if not res1 else 0
        output -= 2 if not res2 else 0
    return {'response': output}
