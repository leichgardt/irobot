import os
import asyncio
from urllib.parse import urlparse, parse_qs
from fastapi import Request
from starlette.responses import Response
from functools import wraps
from datetime import datetime, timedelta
from src.lb import get_payments

from .telegram_api import telegram_api
from src.bot.text import Texts
from src.bot.api import main_menu
from src.utils import alogger as logger, config
from src.sql import sql


class SoloWorker:
    def __init__(self):
        self.permission = {}
        self.announcement = set()

    async def clean_old_pids(self):
        await sql.del_pids()

    async def get_permission(self):
        await asyncio.sleep(2)
        pid = os.getpid()
        await sql.add_pid(pid)
        await asyncio.sleep(5)
        pids = await sql.get_pids()
        if pids:
            pids.sort()
            if pids[0] == pid:
                return True
        return False

    def solo_worker(self, *, name: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if self.permission.get(name) is None:
                    self.permission.update({name: await self.get_permission()})
                if self.permission.get(name):
                    if name not in self.announcement:
                        await logger.info(f'Solo worker "{name}" starts in [{os.getpid()}]')
                        self.announcement.add(name)
                    return await func(*args, **kwargs)
            return wrapper
        return decorator


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
                text, parse, res = Texts.payments_online_success, Texts.payments_online_success.parse_mode, 'finished'
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
        await telegram_api.send_message(sql_data[1], text, parse, reply_markup=main_menu)
        return 0
    return -1


async def auto_payment_monitor():
    await sql.cancel_old_new_payments()
    payments = await sql.find_processing_payments()
    if payments:
        for pay_id, hash_code, chat_id, upd_date, agrm, amount, notified in payments:
            if datetime.now() - upd_date > timedelta(hours=12):
                await sql.upd_payment(hash_code, status='canceled')
                logger.info(f'Payment monitor: canceled [{pay_id}]')
            else:
                agrm_id = await sql.get_agrm_id(chat_id, agrm)
                for payment in await get_payments(agrm_id, minutes=30):
                    if not await sql.find_payments_by_record_id(payment.pay.recordid):
                        if abs((float(payment.amountcurr) / float(amount)) - 1) < 0.01:
                            text, parse = Texts.payments_online_success, Texts.payments_online_success.parse_mode
                            if not notified:
                                await telegram_api.send_message(chat_id, text, parse, reply_markup=main_menu)
                                await sql.upd_payment(hash_code, status='finished', record_id=payment.pay.recordid,
                                                      notified=True)
                            else:
                                await sql.upd_payment(hash_code, status='finished', record_id=payment.pay.recordid)
                            logger.info(f'Payment monitor: finished [{pay_id}]')
                            break
