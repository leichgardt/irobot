from fastapi import Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from src.modules import lb, sql, Texts
from src.web import GlobalDict
from src.web.schemas.login import LoginItem
from src.web.schemas.router import MyAPIRouter
from src.web.utils.login import logining


default_context = GlobalDict('web-default-context')
default_params = GlobalDict('web-default-parameters')
router = MyAPIRouter()
templates = Jinja2Templates(directory='templates')


@router.get('/login')
async def login_page(request: Request, hash_code: str = None):
    if hash_code and await sql.find_chat_by_hash(hash_code):
        context = dict(request=request, title=Texts.web.auth, hash_code=hash_code, **default_context)
        return templates.TemplateResponse('user/login.html', context, headers=default_params['headers'])
    message = {'title': Texts.web.error, 'textlines': Texts.web.login_try_again}
    context = dict(request=request, title=Texts.web.auth, message=message, **default_context)
    return templates.TemplateResponse('user/page.html', context, headers=default_params['headers'])


@router.post('/api/login')
async def login_try_request(response: Response, background_tasks: BackgroundTasks, item: LoginItem):
    """
    Коды ответа:
         1 - успешная авторизация
         2 - договор уже добавлен к учётной записи
         0 - неверный пароль
        -1 - договор не найден
        -2 - не переданы данные (agrm/password/hash)
    """
    if item.login and item.pwd and item.hash:
        res = await lb.check_account_pass(item.login, item.pwd)
        if res == 1:
            chat_id = await sql.find_chat_by_hash(item.hash)
            if chat_id:
                if item.login in await sql.get_accounts(chat_id):
                    await router.logger.info(f'Login: account already added [{chat_id}]')
                    return {'response': 2}
                await router.logger.info(f'Logining [{chat_id}]')
                background_tasks.add_task(logining, chat_id, item.login)
                response.status_code = 202
                return {'response': 1}
            else:
                await router.logger.info(f'Login: chat_id not found [{item.login}]')
                return {'response': -1}
        elif res == 0:
            await router.logger.info(f'Login: incorrect login or pwd [{item.login}]')
            return {'response': 0}
        else:
            await router.logger.info(f'Login: error [{item.login}]')
            return {'response': -1}
    return {'response': -2}


@router.get('/login_success')
async def successful_login_page(request: Request):
    message = dict(title=Texts.web.auth_success)
    context = dict(request=request, title=Texts.web.auth, message=message, **default_context)
    return templates.TemplateResponse('user/page.html', context, headers=default_params['headers'])
