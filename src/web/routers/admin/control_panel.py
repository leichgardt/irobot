from fastapi import Request, Depends
from fastapi.responses import RedirectResponse

from src.web import lan_require, get_context, GlobalDict, get_request_data
from src.web.routers.admin.admin_router import router, templates
from src.web.schemas import ops
from src.web.utils import ops as ops_utils
from src.web.utils.dependecies import get_current_oper


monitor_flags = GlobalDict('solo-worker-flags')


@router.get('/control_panel')
@lan_require
async def control_panel_page(request: Request):
    if request.cookies.get('irobot_access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['irobot_access_token'])
        if oper:
            if not oper.root:
                return RedirectResponse('chat')
            else:
                context = get_context(request, oper=oper.dict(), monitors=monitor_flags)
                return templates.TemplateResponse(f'admin/control_panel.html', context)
    return RedirectResponse('auth')


@router.post('/api/switch_monitor')
@lan_require
async def switch_monitor_request(request: Request, __: ops.Oper = Depends(get_current_oper)):
    data = await get_request_data(request)
    monitor_flags[data['monitor']] = not monitor_flags[data['monitor']]
    return {'response': 1, 'enabled': monitor_flags[data['monitor']]}
