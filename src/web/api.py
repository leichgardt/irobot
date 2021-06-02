from urllib.parse import urlparse, parse_qs
from fastapi import Request
from starlette.responses import Response
from functools import wraps

from .telegram_api import telegram_api
from src.bot.text import Texts
from src.bot.api import main_menu
from src.utils import alogger as logger, config
from src.sql import sql


async def get_request_data(request: Request):
    if request.method == 'GET':
        data = request.query_params
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
        if ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip[:8] == '192.168.' or \
                ip == config['paladin']['ironnet-global']:
            return await func(request, *args, **kwargs)
        else:
            logger.info(f'Access denied for {ip}')
            return Response(status_code=403)
    return wrapper


def get_query_params(url):
    return parse_qs(urlparse(url).query)


async def handle_payment_response(result, hash_id):
    data = await sql.find_payment(hash_id)
    if data:
        payment_id, chat_id, url, status, inline, agrm, amount, notified = data
        if status == 'processing':
            if result == 'success':
                text, parse, res = Texts.payments_online_success, Texts.payments_online_success.parse_mode, 'success'
            elif result == 'fail':
                text, parse, res = Texts.payments_online_fail, Texts.payments_online_fail.parse_mode, 'fail'
            else:
                await logger.fatal(f'Payment error!!! Incorrect result. Payment_id: {payment_id}')
                text, parse, res = Texts.payment_error, Texts.payment_error.parse_mode, 'error'
            if not notified:
                await telegram_api.send_message(chat_id, text, parse, reply_markup=main_menu)
                await sql.upd_payment(hash_id, status=res, notified=True)
            else:
                await sql.upd_payment(hash_id, status=res)
        return 1  # платёж найден и сообщение в телеграм отправлено
    return 0


async def edit_message(chat_id, message_id, text, parse_mode=None, reply_markup=None):
    try:
        await telegram_api.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=reply_markup)
    except:
        await telegram_api.send_message(chat_id, text, parse_mode, reply_markup=reply_markup)


async def delete_message(chat_id, message_id):
    try:
        await telegram_api.delete_message(chat_id, message_id)
    except:
        pass

