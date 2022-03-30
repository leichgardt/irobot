import traceback

from aiologger import Logger
from fastapi import Request
from fastapi.templating import Jinja2Templates
from functools import wraps
from ipaddress import ip_address, ip_network
from starlette.responses import Response
from urllib.parse import urlparse, parse_qs

from src.bot import keyboards
from src.bot.api import get_all_agrm_data, Keyboard
from src.lb import lb
from src.parameters import HOST_IP_LIST
from src.sql import sql
from src.text import Texts
from src.web.table import Table
from src.web.telegram_api import send_message, edit_inline_message, delete_message, send_chat_action


__all__ = (
    'get_query_params',
    'get_request_data',
    'lan_require',
    'broadcast',
    'logining',
    'get_subscriber_table',
    'get_mailing_history',
    'message_distribute'
)


async def get_request_data(request: Request):
    """ Получить переданные данные из запроса (типа: JSON, FORM, QUERY_PARAMS)"""
    if request.method == 'GET':
        data = request.query_params
    else:
        try:
            data = await request.json()
        except:
            data = await request.form()
    return dict(data) if data else {}


def lan_require(func):
    """ Декоратор-ограничитель: разрешает доступ, если IP-адрес запроса из локальной сети или от сервера """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        ip = request.client.host or '127.0.0.1'
        lan_networks = [ip_network('192.168.0.0/16'), ip_network('172.16.0.0/12'), ip_network('10.0.0.0/8')]
        if (ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip in HOST_IP_LIST or
                [True for network in lan_networks if ip_address(ip) in network]):
            return await func(request, *args, **kwargs)
        else:
            return Response(status_code=403)
    return wrapper


def get_query_params(url):
    """ Парсинг параметров URL запроса """
    return parse_qs(urlparse(url).query)


async def logining(chat_id: int, login: str):
    """ Авторизация пользователя по chat_id и логину от Личного Кабинета (ЛК) """
    await send_chat_action(chat_id, 'typing')
    user_id = await lb.get_user_id_by_login(login)
    await sql.add_account(chat_id, login, user_id)
    await sql.upd_hash(chat_id, None)
    if not await sql.get_sub(chat_id):
        # если пользователь новый
        await sql.subscribe(chat_id)
        inline, _, _ = await sql.get_inline_message(chat_id)
        await delete_message(chat_id, inline)
        text, parse_mode = Texts.auth_success.pair()
        await send_message(chat_id, text.format(account=login), parse_mode, reply_markup=keyboards.main_menu_kb)
    else:
        # если пользователь добавил новый аккаунт
        text, parse_mode = Texts.settings_account_add_success.pair()
        await edit_inline_message(chat_id, text.format(account=login), parse_mode)
        data = await get_all_agrm_data(chat_id, only_numbers=True)
        text, parse_mode = Texts.settings_accounts.pair(accounts=Texts.get_account_agrm_list(data))
        btn_list = await keyboards.get_agrms_btn(custom=data, prefix='account') + [keyboards.account_settings_btn]
        kb = Keyboard(btn_list).inline()
        await send_message(chat_id, text, parse_mode, reply_markup=kb)


async def broadcast(data: dict, logger: Logger):
    """
    Функция массовой рассылки сообщений пользователям бота. Запускается через web-интерфейс

    Формат данных `data` {
        id: int                 - ID записи в БД в таблице irobot.mailings,
        type: str               - тип рассылка сообщения
        targets: list or None,  - список целей (для типов "direct", "user_id", "agrm_id", "agrm")
        text: str               - текст сообщения
        parse_mode: str         - метод парсинга для форматирования текста (html, markdown, markdown_v2, ...)
    }
    """
    if data:
        await sql.upd_mailing_status(data['id'], 'processing')
        try:
            if data['type'] == 'notify':
                targets = [data[0] for data in await sql.get_subs() if data]
            elif data['type'] == 'mailing':
                targets = [data[0] for data in await sql.get_subs(mailing=True) if data]
            elif data['type'] == 'direct':
                targets = data['targets']
            else:
                await logger.warning(f'Broadcast error [{data["id"]}]: wrong mail type ID "{data["type"]}"')
                await sql.upd_mailing_status(data['id'], 'error')
                return 0
        except Exception as e:
            await logger.error(f'Broadcast error [{data.get("id", 0) or data}]: {e}\n{traceback.format_exc()}')
            if data.get('id', 0):
                await sql.upd_mailing_status(data.get('id', 0), 'failed')
        else:
            if targets:
                for chat_id in set(targets):
                    await send_message(chat_id, data['text'], parse_mode=data['parse_mode'])
                await sql.upd_mailing_status(data['id'], 'complete')
            else:
                await logger.warning(f'Broadcast error [{data["id"]}]: failed to get targets {data["targets"]}')
                await sql.upd_mailing_status(data['id'], 'missed')


async def get_subscriber_table():
    accs = await sql.get_sub_accounts()
    if accs:
        data = {}
        for chat_id, login, mailing in accs:
            if chat_id not in data:
                data[chat_id] = dict(accounts=login, mailing=mailing)
            else:
                data[chat_id]['accounts'] = data[chat_id]['accounts'] + '<br/>' + login
        table = Table([[key, value['mailing'], value['accounts']] for key, value in data.items()])
        for line in table:
            if not line[1].value:
                line[1].style = 'background-color: red;'
            else:
                line[1].style = 'background-color: green; color: white;'
        return table.get_html()


async def get_mailing_history():
    res = await sql.get_mailings()
    if res:
        table = Table(res)
        for line in table:
            line[4].value = '\n'.join(line[4].value) if isinstance(line[4].value, list) else line[4].value
        return table.get_html()


async def message_distribute(text, parse_mode, target_type, target):
    mail_id, targets = 0, []
    if target_type == 'user_id':
        targets = [chat_id for uid in targets for chat_id in await sql.find_user_chats(uid)]
    elif target_type == 'chat_id':
        targets = [target]
    elif target_type in ['agrm_id', 'agrm']:
        accounts = await lb.direct_request('getAccounts',
                                           {'agrmid': target} if target_type == 'agrmid' else {'agrmnum': target})
        targets = [chat_id for acc in accounts for chat_id in await sql.find_user_chats(acc.account.uid)]
    if targets:
        mail_id = await sql.add_mailing('direct', text, list(set(targets)), parse_mode)
    return mail_id, targets


if __name__ == '__main__':
    import asyncio
    res = asyncio.run(get_mailing_history())
    print(res)
