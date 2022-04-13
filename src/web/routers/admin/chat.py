from aiologger import Logger
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.web.utils import connection_manager, chat as chat_utils, ops as ops_utils
from src.web.utils.api import get_request_data, lan_require, get_context


router = APIRouter(prefix='/admin')
router.logger = Logger.with_default_handlers()
templates = Jinja2Templates(directory='templates')
manager = connection_manager.ConnectionManager()


@router.get('/chat')
@lan_require
async def admin_page(request: Request):
    if request.cookies.get('access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['access_token'])
        if oper:
            context = get_context(request, oper=oper.dict())
            return templates.TemplateResponse(f'admin/chat.html', context)
    return RedirectResponse('/admin/')


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, access_token: str):
    oper = await ops_utils.get_oper_by_token(access_token)
    if oper:
        await manager.connect(websocket, oper.oper_id)
        chats = await chat_utils.get_accounts_and_chats()
        await websocket.send_json({'action': 'get_chats', 'data': chats})
        try:
            while True:
                input_data = await websocket.receive_json()
                action = input_data.get('action')
                data = input_data.get('data')
                if action == 'get_chats':
                    chats = await chat_utils.get_accounts_and_chats()
                    await websocket.send_json({'action': 'get_chats', 'data': chats})
                elif action in ('get_chat', 'load_messages'):
                    output = await chat_utils.get_chat_messages(data['chat_id'], data['message_id'])
                    await websocket.send_json({'action': action, 'data': output})
                elif action == 'send_message':
                    msg = await chat_utils.send_oper_message(data, oper.oper_id, oper.full_name)
                    await manager.broadcast('get_message', msg, firstly=websocket)
                elif action == 'take_chat':
                    await chat_utils.take_chat(data, oper.oper_id)
                    output = {'chat_id': data, 'oper_id': oper.oper_id, 'oper_name': oper.full_name}
                    await manager.broadcast('take_chat', output, firstly=websocket)
                elif action == 'drop_chat':
                    await chat_utils.drop_chat(data, oper.oper_id)
                    output = {'chat_id': data, 'oper_id': oper.oper_id}
                    await manager.broadcast('drop_chat', output, firstly=websocket)
                elif action == 'finish_support':
                    msg = await chat_utils.finish_support(data, oper.oper_id, oper.full_name)
                    output = {'chat_id': data, 'oper_id': oper.oper_id}
                    await manager.broadcast('get_message', msg, firstly=websocket)
                    await manager.broadcast('finish_support', output, firstly=websocket)
                    # todo show results: messages count, time left, operators in the support
                elif action == 'read_chat':
                    await chat_utils.read_chat(data)
                    chats = await chat_utils.get_accounts_and_chats()
                    await manager.broadcast('get_chats', chats, ignore_list=[websocket])
                else:
                    print('ws received data:', data)
                    await websocket.send_json({'action': 'answer', 'data': 'data received'})
        except WebSocketDisconnect:
            manager.remove(websocket)
