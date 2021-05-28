from .telegram_api import telegram_api
from src.bot.text import Texts
from src.bot.api import main_menu
from src.utils import flogger as logger


async def handle_payment_response(sql, result, hash_id):
    payment_id, chat_id, _, status, _ = await sql.find_payment(hash_id)
    if payment_id:
        if status == 'new':
            if result == 'success':
                text, parse, res = Texts.payments_online_success, Texts.payments_online_success.parse_mode, 'success'
            elif result == 'fail':
                text, parse, res = Texts.payments_online_fail, Texts.payments_online_fail.parse_mode, 'fail'
            else:
                logger.fatal(f'Payment error!!! Id: {payment_id}')
                text, parse, res = Texts.payment_error, Texts.payment_error.parse_mode, 'error'
            await sql.upd_payment_status(hash_id, res)
        else:
            logger.error(f'Payment error! Already completed. Id: {payment_id}')
            text, parse = Texts.payment_error, Texts.payment_error.parse_mode
        await telegram_api.send_message(chat_id, text, parse, reply_markup=main_menu)
        return 1
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

