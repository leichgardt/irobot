from datetime import datetime
from pprint import pprint

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

from src.parameters import ABOUT, VERSION
from src.sql import sql
from src.web import (
    lan_require,
    get_request_data,
    webhook_request,
    send_message,
    get_subscriber_table,
    get_mailing_history,
    ConnectionManager,
    get_profile_photo
)
from src.web.schemas import opers
from src.web.utils import opers as opers_utils
from src.web.utils.dependecies import get_current_oper


router = APIRouter(prefix='/admin')
templates = Jinja2Templates(directory='templates')
manager = ConnectionManager()


@router.get('/')
@lan_require
async def index_page(request: Request):
    context = {
        'request': request,
        'timestamp': int(datetime.now().timestamp()),
        'title': 'Admin',
        'about': ABOUT,
        'version': VERSION,
        'oper': {}
    }
    if 'access_token' in request.cookies:
        oper = await get_current_oper(request.cookies['access_token'])
        if oper:
            context['oper'] = oper
    return templates.TemplateResponse(f'admin/index.html', context)


@router.post('/api/sign-up', response_model=opers.Oper)
@lan_require
async def sign_up_request(request: Request, oper: opers.OperCreate):
    db_oper = await opers_utils.get_oper_by_login(oper.login)
    if db_oper:
        raise HTTPException(status_code=400, detail='Login already registered')
    return await opers_utils.create_oper(oper)


@router.post('/api/auth', response_model=opers.TokenBase)
@lan_require
async def auth_request(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    oper = await opers_utils.get_oper_by_login(form_data.username)
    print('oper', oper)
    if not oper:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not opers_utils.validate_password(form_data.password, oper['hashed_password']):
        raise HTTPException(status_code=400, detail='Incorrect email or password')
    token = await opers_utils.create_oper_token(oper['oper_id'])
    print('token', token)
    return token


@router.post('/api/me', response_model=opers.OperBase)
@lan_require
async def read_opers_me(request: Request, current_oper: opers.Oper = Depends(get_current_oper)):
    return current_oper


@router.get('/api/get_mailing_data')
@lan_require
async def get_mailing_data(request: Request, _: opers.Oper = Depends(get_current_oper)):
    return {'response': 1, 'table': await get_mailing_history(), 'subs': await get_subscriber_table()}


async def select_chat(data):
    res = await sql.execute(
        'select message_id, datetime, from_oper, content_type, content from irobot.support_messages '
        'where chat_id=%s order by datetime desc offset %s limit 10', data['chat_id'], data['page'] * 10, as_dict=True
    )
    for chat in res:
        chat.update({'datetime': chat['datetime'].strftime('%Y-%m-%d %H:%M:%S')})
    res.reverse()
    return res


async def send_oper_message(data, oper_id):
    res = await send_message(data['chat_id'], data['text'])
    if res and res.message_id > 0:
        date = await sql.insert(
            'insert into irobot.support_messages (chat_id, message_id, from_oper, content_type, content) values ('
            '%s, %s, %s, %s, %s) returning datetime', data['chat_id'], res.message_id, oper_id, 'text',
            {'text': data['text']}
        )
        return {
            'message_id': res.message_id,
            'datetime': date.strftime('%Y-%m-%d %H:%M:%S'),
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


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, access_token: str):
    oper = await opers_utils.get_oper_by_token(access_token)
    print('ws token', access_token, 'oper_id', oper['oper_id'])
    await manager.connect(websocket, oper)
    if oper:
        chats = await sql.get_support_dialog_list()
        await websocket.send_json({'action': 'get_chats', 'data': chats})
        try:
            while True:
                data = await websocket.receive_json()
                if data['action'] == 'get_chat':
                    res = await select_chat(data['data'])
                    await websocket.send_json({'action': 'get_chat', 'data': res})
                elif data['action'] == 'send_message':
                    msg = await send_oper_message(data['data'], oper['oper_id'])
                    if msg:
                        await websocket.send_json({'action': 'get_message', 'data': msg})
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


@router.on_event('startup')
@repeat_every(seconds=30)
async def olo_monitor():
    await manager.broadcast('broadcast', {'text': f'Broadcast elmav'})
