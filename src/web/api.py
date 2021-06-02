from .telegram_api import telegram_api
from src.bot.text import Texts
from src.bot.api import main_menu
from src.utils import alogger as logger
from src.sql import sql


async def handle_payment_response(result, hash_id):
    data = await sql.find_payment(hash_id)
    if data:
        payment_id, chat_id, url, status, inline, agrm, amount, balance = data
        if status in ['processing']:
            if result == 'success':
                text, parse, res = Texts.payments_online_success, Texts.payments_online_success.parse_mode, 'success'
            elif result == 'fail':
                text, parse, res = Texts.payments_online_fail, Texts.payments_online_fail.parse_mode, 'fail'
            else:
                await logger.fatal(f'Payment error!!! Incorrect result. Payment_id: {payment_id}')
                text, parse, res = Texts.payment_error, Texts.payment_error.parse_mode, 'unknown'
        else:
            await logger.error(f'Payment error! Already completed. Payment_id: {payment_id}')
            text, parse, res = Texts.payment_error, Texts.payment_error.parse_mode, 'error'
        await telegram_api.send_message(chat_id, text, parse, reply_markup=main_menu)
        await sql.upd_payment(hash_id, status=res, notified=True)
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

