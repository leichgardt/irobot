from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse

from src.web.routers.admin.admin_router import router, templates
from src.web.utils import connection_manager, chat as chat_utils, ops as ops_utils, chat_actions
from src.web.utils.api import lan_require, get_context


router.manager = connection_manager.ConnectionManager()


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
    if oper:
        try:
            await router.manager.connect(websocket, oper.oper_id)
            chats = await chat_utils.get_accounts_and_chats()
            await websocket.send_json({'action': 'get_chats', 'data': chats})
            while True:
                input_data = await websocket.receive_json()
                action = input_data.get('action')
                data = input_data.get('data')
                if action and data:
                    func = chat_actions.actions.get_func(action)
                    if func:
                        await func(websocket, router.manager, oper, data)
                    else:
                        await router.logger.warning(f'Received unknown action "{action}" from {oper.login}')
                else:
                    print('ws received data:', input_data)
                    await websocket.send_json({'action': 'answer', 'data': 'data received'})
        except WebSocketDisconnect:
            router.manager.remove(websocket, oper.oper_id)
        except Exception as e:
            if 'ConnectionClosedError' in str(e) or "after sending 'websocket.close'" in str(e):
                router.manager.remove(websocket, oper.oper_id)
            else:
                await router.logger.exception(f'WebSocket error for oper={oper.oper_id}: {e}')
