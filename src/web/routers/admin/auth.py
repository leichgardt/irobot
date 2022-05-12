from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from src.web.schemas import ops
from src.web.schemas.router import MyAPIRouter
from src.web.utils import ops as ops_utils
from src.web.utils.api import lan_require, get_context
from src.web.utils.dependecies import get_current_oper


router = MyAPIRouter(prefix='/admin')
templates = Jinja2Templates(directory='templates')


@router.get('/')
@router.get('/auth')
@lan_require
async def auth_page(request: Request):
    context = get_context(request)
    if request.cookies.get('irobot_access_token'):
        oper = await ops_utils.get_oper_by_token(request.cookies['irobot_access_token'])
        if oper:
            context['oper'] = oper.dict()
            return RedirectResponse('chat')
    context['pages'] = []
    return templates.TemplateResponse(f'admin/auth.html', context)


@router.post('/api/sign-up', response_model=ops.OperBase)
@lan_require
async def sign_up_request(_: Request, new_oper: ops.OperCreate, current_oper: ops.Oper = Depends(get_current_oper)):
    """ Создать нового оператора (только для администраторов) """
    if not current_oper.root:
        raise HTTPException(status_code=400, detail='Not permitted')
    db_oper = await ops_utils.get_oper_by_login(new_oper.login)
    if db_oper:
        raise HTTPException(status_code=400, detail=f'Operator "{new_oper.login}" already registered')
    await router.logger.info(f'Registration of a new operator by {current_oper.login}: {new_oper.login}')
    return await ops_utils.create_oper(new_oper)


@router.post('/api/change-password')
@lan_require
async def sign_up_request(_: Request, data: ops.NewPassword, current_oper: ops.OperBase = Depends(get_current_oper)):
    db_oper = await ops_utils.get_oper_by_login(current_oper.login)
    if not ops_utils.validate_password(data.password, db_oper['hashed_password']):
        raise HTTPException(status_code=400, detail='Incorrect password')
    await router.logger.info(f'Password changed: {current_oper.login}')
    return await ops_utils.set_new_password(db_oper['oper_id'], data.new_password)


@router.post('/api/auth', response_model=ops.Oper)
@lan_require
async def auth_request(_: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    db_oper = await ops_utils.get_oper_by_login(form_data.username)
    if not db_oper:
        raise HTTPException(status_code=400, detail='Incorrect login or password')
    if not ops_utils.validate_password(form_data.password, db_oper['hashed_password']):
        raise HTTPException(status_code=400, detail='Incorrect login or password')
    token = await ops_utils.create_oper_token(db_oper['oper_id'])
    return {**db_oper, 'token': token}
