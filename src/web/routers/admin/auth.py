from aiologger import Logger
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from src.web.schemas import ops
from src.web.utils import ops as ops_utils
from src.web.utils.api import lan_require, get_context
from src.web.utils.dependecies import get_current_oper


router = APIRouter(prefix='/admin')
router.logger = Logger.with_default_handlers()
templates = Jinja2Templates(directory='templates')


@router.get('/')
@lan_require
async def auth_page(request: Request):
    context = get_context(request)
    if request.cookies.get('access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['access_token'])
        if oper:
            context['oper'] = oper.dict()
            return RedirectResponse('chat')
    context['pages'] = []
    return templates.TemplateResponse(f'admin/auth.html', context)


@router.post('/api/sign-up', response_model=ops.Oper)
@lan_require
async def sign_up_request(_: Request, oper: ops.OperCreate):
    db_oper = await ops_utils.get_oper_by_login(oper.login)
    if db_oper:
        raise HTTPException(status_code=400, detail='Login already registered')
    return await ops_utils.create_oper(oper)


@router.post('/api/auth', response_model=ops.Oper)
@lan_require
async def auth_request(_: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    oper = await ops_utils.get_oper_by_login(form_data.username)
    if not oper:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not ops_utils.validate_password(form_data.password, oper['hashed_password']):
        raise HTTPException(status_code=400, detail='Incorrect email or password')
    token = await ops_utils.create_oper_token(oper['oper_id'])
    return {**oper, 'token': token}
