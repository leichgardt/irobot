from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from websockets.exceptions import ConnectionClosedOK

from src.modules import cache_server
from src.web.schemas.router import MyAPIRouter
from src.web.utils import ops as ops_utils, chat as chat_utils
from src.web.utils.api import lan_require, get_context
from src.web.utils.chat_connector import ChatConnector
from src.web.utils.connection_manager import ConnectionManager


router = MyAPIRouter(prefix='/admin')
templates = Jinja2Templates(directory='templates')
manager = ConnectionManager(cache_server)


@router.get('/chat')
@lan_require
async def admin_page(request: Request):
    if request.cookies.get('irobot_access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['irobot_access_token'])
        if oper:
            context = get_context(request, oper=oper.dict())
            return templates.TemplateResponse(f'admin/chat.html', context)
    return RedirectResponse('auth')


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, access_token: str):
    oper = await ops_utils.get_oper_by_token(access_token)
    if not oper:
        return
    try:
        await manager.connect(websocket, oper.oper_id)
        chats = await chat_utils.get_accounts_and_chats()
        await websocket.send_json({'action': 'get_chats', 'data': chats})
    except (WebSocketDisconnect, ConnectionClosedOK):
        await manager.remove(websocket, oper.oper_id)
    else:
        connector = ChatConnector(manager, websocket, oper, router.logger, cache_server)
        await connector.handle_connection()
        await manager.remove(websocket, oper.oper_id)
