from datetime import datetime, timedelta

from src.text import Texts
from src.bot.api import main_menu
from src.lb import lb
from src.sql import sql
from src.web.userside import USPipe
from src.web.telegram_api import send_feedback, send_message, delete_message


async def auto_payment_monitor(logger):
    payments = await sql.find_processing_payments()
    if payments:
        await sql.cancel_old_new_payments()
        for pay_id, hash_code, chat_id, upd_date, agrm, amount, notified, inline in payments:
            if datetime.now() - upd_date > timedelta(hours=24):
                await sql.upd_payment(hash_code, status='canceled')
                logger.info(f'Payment monitor: canceled [{pay_id}]')
            else:
                for lb_payment in await lb.get_payments(agrm, days=1):  # загрузить из биллинга платежи за 1 сутки
                    if not await sql.find_payments_by_record_id(lb_payment.pay.recordid):
                        if abs(float(lb_payment.amountcurr) - float(amount)) <= 0.01:
                            text, parse = Texts.payments_online_success, Texts.payments_online_success.parse_mode
                            if not notified:
                                await delete_message(chat_id, inline)
                                await send_message(chat_id, text, parse, reply_markup=main_menu)
                                await sql.upd_payment(hash_code, status='finished', record_id=lb_payment.pay.recordid,
                                                      notified=True)
                            else:
                                await sql.upd_payment(hash_code, status='finished', record_id=lb_payment.pay.recordid)
                            logger.info(f'Payment monitor: finished [{pay_id}]')
                            break


async def auto_feedback_monitor(logger):
    res = await sql.get_feedback('new', '1 hour')  # new - sent - rated - complete - commented
    if res:
        for fb_id, task_id, chat_id in res:
            # если задание в cardinalis еще не завершено, то отправляем сообщение
            # если сообщение отправлено, то переводим feedback в статус 'sent'
            if await _is_task_uncompleted(task_id):
                if await send_feedback(chat_id, task_id):
                    await sql.upd_feedback(fb_id, status='sent')
                    logger.info(f'Feedback sent [{chat_id}]')
            else:
                await sql.upd_feedback(fb_id, status='passed')
                logger.info(f'Feedback already closed [{chat_id}]')


async def rates_feedback_monitor(logger):
    res = await sql.get_feedback('rated', '1 hour')
    if res:
        for fb_id, task_id, chat_id in res:
            await sql.upd_feedback(fb_id, status='complete')
            logger.info(f'Rated feedback completed due to Timeout [{chat_id}]')


async def _is_task_uncompleted(task_id):
    if not await sql.find_uncompleted_task(task_id):
        await sql.finish_feedback_task(task_id)
        return False
    us = USPipe()
    fb_task = await us.get_feedback_task(task_id)
    if fb_task and fb_task.get('state', {}).get('id') == 2:  # если оно уже выполнено
        return False
    return True
