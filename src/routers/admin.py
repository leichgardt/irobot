from datetime import datetime

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from src.parameters import ABOUT, VERSION
from src.sql import sql
from src.web import (
    get_request_data,
    lan_require,
    send_message,
    get_subscriber_table,
    get_mailing_history,
    ConnectionManager,
)
from src.web.schemas import ops
from src.web.utils import ops as ops_utils
from src.web.utils.dependecies import get_current_oper


router = APIRouter(prefix='/admin')
templates = Jinja2Templates(directory='templates')
manager = ConnectionManager()


def get_context(request: Request, **kwargs):
    return {
        'request': request,
        'timestamp': int(datetime.now().timestamp()),
        'title': 'Irobot Admin',
        'pages': [
            {'title': 'Чат', 'url': 'chat'},
            {'title': 'Рассылка', 'url': 'mailing'},
        ],
        'about': ABOUT,
        'version': VERSION,
        'oper': {},
        **kwargs
    }


@router.get('/')
@lan_require
async def auth_page(request: Request):
    context = get_context(request)
    if request.cookies.get('access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['access_token'])
        if oper:
            context['oper'] = oper
            return RedirectResponse('chat')
    return templates.TemplateResponse(f'admin/auth.html', context)


@router.post('/api/sign-up', response_model=ops.Oper)
@lan_require
async def sign_up_request(_: Request, oper: ops.OperCreate):
    db_oper = await ops_utils.get_oper_by_login(oper.login)
    if db_oper:
        raise HTTPException(status_code=400, detail='Login already registered')
    return await ops_utils.create_oper(oper)


@router.post('/api/auth', response_model=ops.TokenBase)
@lan_require
async def auth_request(_: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    oper = await ops_utils.get_oper_by_login(form_data.username)
    if not oper:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not ops_utils.validate_password(form_data.password, oper['hashed_password']):
        raise HTTPException(status_code=400, detail='Incorrect email or password')
    token = await ops_utils.create_oper_token(oper['oper_id'])
    return token


@router.post('/api/me', response_model=ops.OperBase)
@lan_require
async def get_oper_me(_: Request, current_oper: ops.Oper = Depends(get_current_oper)):
    return current_oper


@router.get('/api/get_mailing_data')
@lan_require
async def get_mailing_data(_: Request, __: ops.Oper = Depends(get_current_oper)):
    return {'response': 1, 'table': await get_mailing_history(), 'subs': await get_subscriber_table()}


@router.get('/chat')
@router.get('/mailing')
@lan_require
async def admin_page(request: Request):
    if request.cookies.get('access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['access_token'])
        if oper:
            context = get_context(request, oper=oper)
            if '/admin/chat' in str(request.url):
                return templates.TemplateResponse(f'admin/chat.html', context)
            else:
                return templates.TemplateResponse(f'admin/mailing.html', context)
    return RedirectResponse('/admin/')


def split_datetime(dt):
    return dt.strftime('%d.%m.%Y'), dt.strftime('%H:%M')


async def get_chat_messages(chat_id, page=0):
    res = await sql.execute(
        'select message_id, datetime, from_oper, content_type, content from irobot.support_messages '
        'where chat_id=%s order by datetime desc offset %s limit 10', chat_id, page * 10, as_dict=True
    )
    for chat in res:
        date, time = split_datetime(chat['datetime'])
        chat.update({'date': date})
        chat.update({'time': time})
        chat.pop('datetime')
    res.reverse()
    return res


async def send_oper_message(data, oper_id):
    res = await send_message(data['chat_id'], data['text'])
    if res and res.message_id > 0:
        dt = await sql.insert(
            'insert into irobot.support_messages (chat_id, message_id, from_oper, content_type, content) '
            'values (%s, %s, %s, %s, %s) returning datetime',
            data['chat_id'], res.message_id, oper_id, 'text', {'text': data['text']}
        )
        date, time = split_datetime(dt)
        return {
            'message_id': res.message_id,
            'date': date,
            'time': time,
            'oper_id': oper_id,
            'content_type': 'text',
            'content': {'text': data['text']}
        }


async def take_chat(chat_id, oper_id):
    res = await sql.execute('select oper_id from irobot.support_chats where chat_id=%s and oper_id is not null',
                            chat_id, as_dict=True)
    if res:
        await manager.send_to_oper(res[0]['oper_id'], {'action': 'drop_chat', 'oper_id': oper_id})
    await sql.update('irobot.support_chats', f'chat_id={chat_id}', oper_id=oper_id)


async def drop_chat(chat_id, oper_id):
    await sql.update('irobot.support_chats', f'chat_id={chat_id} and oper_id={oper_id}', oper_id=None)


async def get_chat_accounts_in_support_need():
    res = await sql.execute(
        'select chat_id, login from irobot.accounts where active=true '
        'and chat_id in (select distinct chat_id from irobot.support_messages)', as_dict=True
    )
    accounts = {}
    for line in res:
        if line['chat_id'] not in accounts:
            accounts[line['chat_id']] = [line['login']]
        else:
            accounts[line['chat_id']].append(line['login'])
    return accounts


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, access_token: str):
    oper = await ops_utils.get_oper_by_token(access_token)
    if oper:
        await manager.connect(websocket, oper['oper_id'])
        chats = await sql.get_support_dialog_list()
        accounts = await get_chat_accounts_in_support_need()
        await websocket.send_json({'action': 'get_chats', 'data': {'chats': chats, 'accounts': accounts}})
        try:
            while True:
                data = await websocket.receive_json()
                if data['action'] == 'get_chat':
                    messages = await get_chat_messages(data['data']['chat_id'], data['data']['page'])
                    await websocket.send_json({'action': 'get_chat', 'data': messages})
                elif data['action'] == 'send_message':
                    msg = await send_oper_message(data['data'], oper['oper_id'])
                    if msg:
                        await websocket.send_json({'action': 'send_message', 'data': msg})
                        msg['chat_id'] = data['data']['chat_id']
                        await manager.broadcast('get_message', msg, ignore_list=[websocket])
                elif data['action'] == 'take_chat':
                    await take_chat(data['data'], oper['oper_id'])
                    await websocket.send_json({'action': 'take_chat', 'data': data['data']})
                elif data['action'] == 'drop_chat':
                    await drop_chat(data['data'], oper['oper_id'])
                    await websocket.send_json({'action': 'drop_chat', 'data': data['data']})
                else:
                    print('ws received data:', data)
                    await websocket.send_json({'action': 'answer', 'data': 'data received'})
        except WebSocketDisconnect:
            manager.remove(websocket)


@router.post('/api/new_message')
@lan_require
async def new_message_request(request: Request):
    data = await get_request_data(request)
    msg = await sql.execute(
        'select chat_id, message_id, datetime, from_oper, content_type, content from irobot.support_messages '
        'where chat_id=%s and message_id=%s limit 1', data['chat_id'], data['message_id'], as_dict=True
    )
    if msg:
        date, time = split_datetime(msg[0]['datetime'])
        msg[0]['date'] = date
        msg[0]['time'] = time
        msg[0].pop('datetime')
        await manager.broadcast('get_message', msg[0])
