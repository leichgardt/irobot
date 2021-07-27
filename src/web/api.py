import asyncio
import traceback
from logging import Logger
from urllib.parse import urlparse, parse_qs
from fastapi import Request
from starlette.responses import Response
from functools import wraps

from src.web.telegram_api import send_message, edit_inline_message, delete_message
from src.bot.text import Texts
from src.bot.api import main_menu, get_keyboard
from src.bot import keyboards
from src.utils import config
from src.sql import sql


async def get_request_data(request: Request):
    if request.method == 'GET':
        data = dict(request.query_params)
    else:
        try:
            data = await request.json()
        except:
            data = await request.form()
    return data if data else {}


def lan_require(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        ip = request.client.host
        if (ip is None or (ip and (ip in ['localhost', '0.0.0.0', '127.0.0.1'] or
                                   ip[:8] == '192.168.' or ip == config['paladin']['ironnet-global']))):
            return await func(request, *args, **kwargs)
        else:
            return Response(status_code=403)
    return wrapper


def get_query_params(url):
    return parse_qs(urlparse(url).query)


async def logining(chat_id, login, agrms_data):
    agrms = []
    for agrm, agrm_id in agrms_data:
        agrms.append(str(agrm))
        await sql.add_agrm(chat_id, agrm, agrm_id)
    agrms = ', '.join(agrms)
    await sql.upd_hash(chat_id, None)
    if not await sql.get_sub(chat_id):
        await sql.subscribe(chat_id)
        inline, _, _ = await sql.get_inline(chat_id)
        await delete_message(chat_id, inline)
        text, parse = Texts.auth_success.format(login=login, agrms=agrms), Texts.auth_success.parse_mode
        await send_message(chat_id, text, parse, reply_markup=main_menu)
    else:
        text, parse = Texts.settings_agrm_add_success.format(login=login, agrms=agrms), Texts.settings_agrm_add_success.parse_mode
        await edit_inline_message(chat_id, text, parse)
        kb = get_keyboard(await keyboards.get_agrms_btn(chat_id), keyboards.agrms_settings_btn)
        await send_message(chat_id, Texts.settings_agrms, Texts.settings_agrms.parse_mode, reply_markup=kb)


async def handle_payment_response(logger, result, hash_id):
    data = await sql.find_payment(hash_id)
    if data:
        payment_id, chat_id, url, status, inline, agrm, amount, notified = data
        if status == 'processing':
            if result == 'success':
                text, parse, res = Texts.payments_online_success, Texts.payments_online_success.parse_mode, 'finished'
            elif result == 'fail':
                text, parse, res = Texts.payments_online_fail, Texts.payments_online_fail.parse_mode, 'fail'
            else:
                logger.fatal(f'Payment error!!! Incorrect result. Payment_id: {payment_id}')
                text, parse, res = Texts.payment_error, Texts.payment_error.parse_mode, 'error'
            if not notified:
                await send_message(chat_id, text, parse, reply_markup=main_menu)
                await sql.upd_payment(hash_id, status=res, notified=True)
            else:
                await sql.upd_payment(hash_id, status=res)
        return 1  # платёж найден и сообщение в телеграм отправлено
    return 0


async def handle_new_payment_request(hash_code, sql_data):
    if sql_data:
        if sql_data[3] in ['new', 'processing']:
            if sql_data[3] == 'new':
                await sql.upd_payment(hash_code, status='processing')
            return 1
        elif sql_data[3] == 'finished':
            text, parse = Texts.payments_online_already_have, Texts.payments_online_already_have.parse_mode
        else:
            text, parse = Texts.payment_error, Texts.payment_error.parse_mode
        await send_message(sql_data[1], text, parse, reply_markup=main_menu)
        return 0
    return -1


async def broadcast(logger: Logger):
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
                    logger.warning(f'Wrong mail_type ID: {m_id}')
                    continue
                if targets:
                    for chat_id, _ in targets:
                        if await send_message(chat_id, text):
                            count += 1
                        await asyncio.sleep(.05)
            except Exception as e:
                logger.error(f'Broadcast error: {e}\nMailing ID: [{m_id}]\n{traceback.format_exc()}')
                await sql.upd_mailing_status(m_id, 'error')
            else:
                await sql.upd_mailing_status(m_id, 'complete')
    return count
