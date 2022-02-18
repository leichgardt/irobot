import asyncio
from datetime import datetime, timedelta

from src.lb import lb
from src.sql import sql
from src.text import Texts
from src.web.userside import USPipe
from src.web.telegram_api import send_feedback, send_message
from src.utils import post_request, config


async def auto_payment_monitor(logger, tries_num=5):
    """
    Поиск некорректных платежей

    Если после оплаты не удалось пополнить счёт через LB API договора сразу - платёж переходит в статус "error".
    Монитор еще `tries_num` раз попытается провести пополнение счёта, и, при сохранении ошибки, переведёт платёж
    в состояние "failure". В таком случае потребуется вмешательство оператора для решения проблемы.

    Также монитор ещё ищет платежы со статусом "processing". Если они находятся в этом статусе более часа, то платёж
    был просрочен - состояние изменится на "timed_out" (для статистики). Если после этого придет ответ от Телеграма
    с `SUCCESSFUL_PAYMENT`, то стандартный процесс пополнения счёта (в модуле l4_payment) инициализиреутся в любом
    случае.
    """
    payments = await sql.find_processing_payments()
    if payments:
        lb_payments = {}
        for payment in payments:
            if payment['status'] == 'success':
                if datetime.now() - payment['update_datetime'] > timedelta(hours=12):
                    await sql.upd_payment(payment['hash'], status='finished')
                else:
                    msg = await send_message(payment['chat_id'], *Texts.payments_online_success.pair())
                    if msg:
                        await sql.upd_payment(payment['hash'], status='finished')
            elif payment['status'] == 'error':
                await logger.info(f'Payment monitor: processing Error Payment (ID={payment["id"]})')
                # обработка платежа, у которого не прошёл платёж в биллинг
                while tries_num > 0:
                    rec_id = await lb.new_payment(payment['agrm'], payment['amount'], payment['receipt'])
                    if rec_id:
                        msg = await send_message(payment['chat_id'], *Texts.payments_online_success.pair())
                        status = 'finished' if msg else 'success'
                        await sql.upd_payment(payment['hash'], status=status, record_id=rec_id)
                        text = 'Payment monitor: Error Payment successful done [{}] (ID={})'
                        await logger.info(text.format(payment['chat_id'], payment['id']))
                        break
                    else:
                        tries_num -= 1
                        if tries_num > 0:
                            await asyncio.sleep(60)
                else:
                    await sql.upd_payment(payment['hash'], status='failure')
                    await logger.warning(f'Payment monitor: FAILURE! Payment ID={payment["id"]}')
                    text = f'Irobot Payment Monitor [FAILURE]\nTries ended\nPayment ID = {payment["id"]}'
                    url = config['paladin']['domain'] + '/tesseract/api/notify'
                    await post_request(url, json=dict(chat_id=config['irobot']['me'], text=text))
            elif payment['status'] == 'processing':
                # обработка платежа, который висит в состоянии 'processing' более часа
                # загрузить платежи из биллинга за последние 1.5 часа и сверить с ними
                if payment['agrm'] not in lb_payments:
                    lb_payments[payment['agrm']] = await lb.get_payments(payment['agrm'], hours=1, minutes=30)
                for lb_pmt in lb_payments[payment['agrm']]:
                    if payment['receipt'] in lb_pmt.pay.receipt:
                        msg = await send_message(payment['chat_id'], *Texts.payments_online_success.pair())
                        status = 'finished' if msg else 'success'
                        await sql.upd_payment(payment['hash'], status=status, record_id=lb_pmt.pay.recordid)
                        break
                else:
                    await sql.upd_payment(payment['hash'], status='timed_out')


async def auto_feedback_monitor(logger):
    """
    Мониторинг feedback-заявок Userside

    Если в БД обнаружена задача на Feedback (в статусе "new"), и если эта заявка еще не выполнена в Userside,
    то выполняется отправка сообщения. Если заявка выполнена в Userside, то задача в БД переходит в статус "passed".
    """
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


async def _is_task_uncompleted(task_id):
    if not await sql.find_uncompleted_task(task_id):
        await sql.finish_feedback_task(task_id)
        return False
    us = USPipe()
    fb_task = await us.get_feedback_task(task_id)
    if fb_task and fb_task.get('state', {}).get('id') == 2:  # если оно уже выполнено
        return False
    return True


async def rates_feedback_monitor(logger):
    """ Монитор незавершенных фидбеков """
    res = await sql.get_feedback('rated', '1 hour')
    if res:
        for fb_id, task_id, chat_id in res:
            await sql.upd_feedback(fb_id, status='complete')
            logger.info(f'Rated feedback completed due to Timeout [{chat_id}]')


if __name__ == '__main__':
    from src.utils import alogger
    asyncio.run(auto_payment_monitor(alogger))
