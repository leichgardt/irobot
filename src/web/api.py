import asyncio
import traceback

from aiologger import Logger
from collections.abc import Iterable
from fastapi import Request
from fastapi.templating import Jinja2Templates
from functools import wraps
from ipaddress import ip_address, ip_network
from starlette.responses import Response
from urllib.parse import urlparse, parse_qs

from src.bot import keyboards
from src.bot.api import main_menu, get_keyboard, get_all_agrm_data, get_payment_url, get_payment_tax
from src.lb import lb
from src.sql import sql
from src.text import Texts
from src.utils import config
from src.web.table import Table
from src.web.telegram_api import send_message, edit_inline_message, delete_message, send_chat_action, edit_message_text


async def edit_payment_message(hash_code, chat_id, agrm, amount, inline):
    summ = amount + (tax := get_payment_tax(amount))
    text, parse = Texts.payments_online_offer.pair(agrm=agrm, amount=amount, tax=tax, res=summ)
    kb = get_keyboard(keyboards.payment_url_btn(get_payment_url(hash_code), summ))
    await edit_message_text(text, chat_id, inline, parse_mode=parse, reply_markup=kb)


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
        if (ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip in config['paladin']['ironnet-global'] or
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
    count = 0
    if data:
        await sql.upd_mailing_status(data['id'], 'processing')
        try:
            if data['type'] == 'notify':
                targets = [data[0] for data in await sql.get_subs() if data]
            elif data['type'] == 'mailing':
                targets = [data[0] for data in await sql.get_subs(mailing=True) if data]
            elif data['type'] == 'direct':
                targets = data['targets']
            elif data['type'] == 'userid':
                targets = [await sql.find_user_chats(uid) for uid in data['targets']]
                targets = [chat_id for group in targets for chat_id in group]
            elif data['type'] in ('agrmid', 'agrm'):
                if data['type'] == 'agrmid':
                    agrm_groups = [await lb.get_account_agrms(agrm_id=agrm_id) for agrm_id in data['targets']]
                else:
                    agrm_groups = [await lb.get_account_agrms(agrm) for agrm in data['targets']]
                groups = [await sql.find_user_chats(agrm['user_id']) for agrms in agrm_groups for agrm in agrms]
                targets = [chat_id for chats in groups for chat_id in chats]
            else:
                await logger.warning(f'Broadcast error [{data["id"]}]: wrong mail type ID "{data["type"]}"')
                await sql.upd_mailing_status(data['id'], 'error')
                return 0
            print(f'{data["targets"]=}, {targets=}')
            if targets:
                for chat_id in set(targets):
                    if await send_message(chat_id, data['text'], parse_mode=data['parse_mode']):
                        count += 1
                    await asyncio.sleep(.05)
            else:
                await logger.warning(f'Broadcast error [{data["id"]}]: undefined targets {targets}')
                await sql.upd_mailing_status(data['id'], 'missed')
        except Exception as e:
            await logger.error(f'Broadcast error [{data.get("id", 0)}]: {e}\n{traceback.format_exc()}')
            if data.get('id', 0):
                await sql.upd_mailing_status(data.get('id', 0), 'error')
        else:
            await sql.upd_mailing_status(data['id'], 'complete')
    return count


class WebM:
    def __init__(self):
        self.templates: Jinja2Templates = None
        self.back_link = ''
        self.bot_name = ''
        self.headers = {}

    def update(self, link, name, headers, templates):
        self.templates = templates
        self.back_link = link
        self.bot_name = name
        self.headers = headers

    def page(self, request: Request, data: dict, *, template: str = 'page.html', **kwargs):
        return self.templates.TemplateResponse(template,
                                               dict(request=request,
                                                    domain=config['paladin']['domain'],
                                                    back_link=self.back_link,
                                                    bot_name=self.bot_name,
                                                    support_bot_name=config['irobot']['chatbot'],
                                                    **data),
                                               headers=self.headers,
                                               **kwargs)
