import asyncio
import traceback

from aiologger import Logger
from fastapi import Request
from functools import wraps
from ipaddress import ip_address, ip_network
from starlette.responses import Response
from urllib.parse import urlparse, parse_qs

from src.bot import keyboards
from src.text import Texts
from src.bot.api import main_menu, get_keyboard, get_all_agrm_data
from src.sql import sql
from src.utils import config
from src.web.telegram_api import send_message, edit_inline_message, delete_message, send_chat_action


async def get_request_data(request: Request):
    """ Получить переданные данные из запроса (типа: JSON, FORM, QUERY_PARAMS)"""
    if request.method == 'GET':
        data = dict(request.query_params)
    else:
        try:
            data = await request.json()
        except:
            data = await request.form()
    return data if data else {}


def lan_require(func):
    """ Декоратор-ограничитель: разрешает доступ, если IP-адрес запроса из локальной сети или от сервера """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        ip = request.client.host or '127.0.0.1'
        lan_networks = [ip_network('192.168.0.0/16'), ip_network('172.16.0.0/12'), ip_network('10.0.0.0/8')]
        if (ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip == config['paladin']['ironnet-global'] or
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
    await sql.add_account(chat_id, login)
    await sql.upd_hash(chat_id, None)
    if not await sql.get_sub(chat_id):
        # если пользователь новый
        await sql.subscribe(chat_id)
        inline, _, _ = await sql.get_inline(chat_id)
        await delete_message(chat_id, inline)
        _, text, parse = Texts.auth_success.full()
        await send_message(chat_id, text.format(account=login), parse, reply_markup=main_menu)
    else:
        # если пользователь добавил новый аккаунт
        _, text, parse = Texts.settings_account_add_success.full()
        await edit_inline_message(chat_id, text.format(account=login), parse)
        data = await get_all_agrm_data(chat_id, only_numbers=True)
        kb = get_keyboard(await keyboards.get_agrms_btn(custom=data, prefix='account'), keyboards.account_settings_btn)
        _, text, parse = Texts.settings_accounts.full()
        await send_message(chat_id, text.format(accounts=Texts.get_account_agrm_list(data)), parse, reply_markup=kb)


async def broadcast(logger: Logger):
    """
    Функция массовой рассылки сообщений пользователям бота. Запускается через Web-интерфейс
    Сообщение для рассылки загружается из БД
    """
    count = 0
    res = await sql.get_new_mailings()
    if res:
        for m_id, mail_type, text in res:
            await sql.upd_mailing_status(m_id, 'processing')
            try:
                if mail_type == 'notify':
                    targets = await sql.get_subs()
                elif mail_type == 'mailing':
                    targets = await sql.get_subs(mailing=True)
                else:
                    await logger.warning(f'Wrong mail_type ID: {m_id}')
                    continue
                if targets:
                    for chat_id, _ in targets:
                        if await send_message(chat_id, text):
                            count += 1
                        await asyncio.sleep(.05)
            except Exception as e:
                await logger.error(f'Broadcast error: {e}\nMailing ID: [{m_id}]\n{traceback.format_exc()}')
                await sql.upd_mailing_status(m_id, 'error')
            else:
                await sql.upd_mailing_status(m_id, 'complete')
    return count
