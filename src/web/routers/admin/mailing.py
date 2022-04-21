from fastapi import Request, Response, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse

from src.modules import sql
from src.web.routers.admin.admin_router import router, templates
from src.web.schemas import ops, mailing
from src.web.schemas.table import Table
from src.web.utils import ops as ops_utils, mailing as mailing_utils
from src.web.utils.api import lan_require, get_context
from src.web.utils.dependecies import get_current_oper


@router.get('/mailing')
@lan_require
async def mailing_page(request: Request):
    if request.cookies.get('irobot_access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['irobot_access_token'])
        if oper:
            context = get_context(request, oper=oper.dict())
            return templates.TemplateResponse(f'admin/mailing.html', context)
    return RedirectResponse('auth')


@router.get('/api/get_mailing_data')
@lan_require
async def get_mailing_data_request(_: Request, __: ops.Oper = Depends(get_current_oper)):
    return {
        'response': 1,
        'table': await mailing_utils.get_mailing_history(),
        'subs': await mailing_utils.get_subscriber_table()
    }


@router.get('/api/get_history')
@lan_require
async def get_history_table_request(_: Request):
    """Получить таблицу с последними 10 рассылками"""
    res = await sql.get_mailings()
    if res:
        table = Table(res)
        for line in table:
            line[4].value = '\n'.join(line[4].value) if isinstance(line[4].value, list) else line[4].value
        return {'response': 1, 'table': table.get_html()}
    return {'response': 0}


@router.post('/api/send_mail')
@lan_require
async def send_mailing_request(
        _: Request,
        response: Response,
        background_tasks: BackgroundTasks,
        item: mailing.Mail
):
    """Добавить новую рассылку"""
    if item.type in ('notify', 'mailing'):
        mail_id = await sql.add_mailing(item.type, item.text)
        if mail_id:
            payload = dict(id=mail_id, type=item.type, text=item.text, parse_mode=item.parse_mode)
            background_tasks.add_task(mailing_utils.broadcast, payload, router.logger)
            await router.logger.info(f'New mailing added [{mail_id}]')
            response.status_code = 202
            return {'response': 1, 'id': mail_id}
        else:
            response.status_code = 500
            await router.logger.error(f'Error of New mailing. Data: {item}')
            return {'response': -1, 'error': 'backand error'}
    else:
        response.status_code = 400
        return {'response': 0, 'error': 'wrong mail_type'}
