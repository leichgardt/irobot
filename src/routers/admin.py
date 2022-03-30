__author__ = 'leichgardt'

import sys
from datetime import datetime
from pathlib import Path
from pprint import pprint

from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every

sys.path.append(str(Path(__file__).parent.parent.resolve()))

from src.parameters import ABOUT, VERSION
from src.sql import sql
from src.web import (
    lan_require,
    get_request_data,
    webhook_request,
    telegram_api,
    get_subscriber_table,
    get_mailing_history,
    ConnectionManager
)


router = APIRouter(prefix='/admin')
templates = Jinja2Templates(directory='templates')
manager = ConnectionManager()


@router.get('/mailing')
@lan_require
async def mailing_page(request: Request):
    table = await get_subscriber_table() or ''
    history = await get_mailing_history() or ''
    context = dict(request=request, title='IroBot', about=ABOUT, version=VERSION,
                   tables=dict(subs=table, history=history))
    return templates.TemplateResponse('mailing.html', context)


@router.get('/')
@lan_require
async def chat_page(request: Request):
    context = dict(request=request, title='IroBot', about=ABOUT, version=VERSION)
    return templates.TemplateResponse('chat.html', context)


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    chat_list = await sql.get_support_dialog_list()
    for i, chat in chat_list.items():
        try:
            res = await telegram_api.get_user_profile_photos(chat['chat_id'], limit=1)
        except:
            continue
        if res['total_count']:
            file = await telegram_api.get_file(res['photos'][0][0]['file_id'])
            chat['photo'] = telegram_api.get_file_url(file['file_path'])
    await websocket.send_json(chat_list)


async def new_message_notify():
    """
    1 определить кто из операторов взял клиента
    2 отправить оператору
    3 или броадкаст
    """
    pass


@router.on_event('startup')
@repeat_every(seconds=2)
async def olo_monitor():
    await manager.broadcast(f'Broadcast elmav {datetime.now()}')


@router.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    try:
        await manager.connect(websocket)
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f'Client {client_id}: {data}')
            print('websocket', websocket, client_id, data)
    except WebSocketDisconnect:
        manager.remove(websocket)


@router.get('/test1')
async def test1_request(request: Request):
    data = await get_request_data(request)
    [print(key, value) for key, value in data.items()]
    return 1


@router.post('/webhook')
async def webhook_gateway(request: Request):
    """
    Шлюз между сервером Telegram и Ботом. Шлюз получает запрос от Telegram, обрабатывает его и передает боту через
    функцию `webhook_request`. А серверу возвращает ответ от бота.
    Шлюз предназначен для введения возможности общаться с пользователями Бота через админку.
    """
    data = await get_request_data(request)
    pprint(data)
    if 'callback_query' not in data:
        res = await sql.execute('SELECT datetime FROM irobot.subs WHERE chat_id=%s AND subscribed=true '
                                'AND support_mode=true', data['message']['chat']['id'])
        if res:
            msg = data['message']
            if 'text' in msg:
                type_ = 'text'
                data = {'entities': msg['entities']} if 'entities' in msg else {}
                data = {'text': msg['text'], **data}
            elif 'document' in msg:
                type_ = 'document'
                data = {'caption': msg['caption']} if 'caption' in msg else {}
                data = {'file_id': msg['document']['file_id'], 'mime_type': msg['document']['mime_type'], **data}
            elif 'photo' in msg:
                type_ = 'photo'
                data = {'caption': msg['caption']} if 'caption' in msg else {}
                data = {'file_id': msg['photo'][-1]['file_id'], **data}
            elif 'sticker' in msg:
                type_ = 'photo'
                data = {'file_id': msg['sticker']['file_id']}
            elif 'voice' in msg:
                type_ = 'voice'
                data = {'file_id': msg['voice']['file_id'], 'mime_type': msg['document']['mime_type']}
            else:
                type_ = 'other'
                data = {k: v for k, v in msg.items() if k not in ('chat', 'date', 'from', 'message_id')}
            await sql.insert('INSERT INTO irobot.support_dialogs (message_id, chat_id, type, data) '
                             'VALUES (%s, %s, %s, %s)', msg['message_id'], msg['chat']['id'], type_, data)
            return {'ok': True}
    res = await webhook_request(data)
    return res
