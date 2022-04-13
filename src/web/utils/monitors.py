import asyncio
from datetime import datetime, timedelta

from aiologger import Logger

from parameters import CARDINALIS_URL, TELEGRAM_NOTIFY_BOT_URL, TELEGRAM_TEST_CHAT_ID
from src.modules import lb, sql, Texts
from src.utils import post_request
from src.web.utils.chat import get_support_list
from src.web.utils.connection_manager import ConnectionManager
from src.web.utils.telegram_api import send_message, get_profile_photo


__all__ = ('auto_feedback_monitor', 'auto_payment_monitor', 'update_all_chat_photo', 'new_messages_monitor')


async def auto_payment_monitor(logger: Logger, tries_num=5):
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
                    await post_request(TELEGRAM_NOTIFY_BOT_URL, json={'chat_id': TELEGRAM_TEST_CHAT_ID, 'text': text},
                                       _logger=logger)
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


async def auto_feedback_monitor(logger: Logger):
    """
    Мониторинг feedback-заявок Userside

    Если в БД обнаружена Feedback-задача (в статусе "sending"/"new"), то она отправляется в запросе в систему сбора
    статистики "Cardinalis". При успехе задача переходит в статус "sent".
    """
    feedbacks = await sql.get_feedback('1 hours')
    if feedbacks:
        for fb_id, chat_id, task_id, rating, comment in feedbacks:
            await logger.info(f'Trying to save Feedback in Cardinalis [{chat_id}] for task [{task_id}]')
            res = await send_feedback_to_cardinalis(logger, task_id, f'{rating}' + (f'\n{comment}' if comment else ''))
            if res > 0:
                await sql.upd_feedback(fb_id, status='complete')
                await logger.info(f'Feedback saved [{chat_id}]')
            elif res == 0:
                await sql.upd_feedback(fb_id, status='passed')
                await logger.info(f'Feedback already closed [{chat_id}]')
            else:
                await logger.warning(f'Failed to save feedback [{chat_id}]')


async def send_feedback_to_cardinalis(logger: Logger, input_task_id: int, input_text: str):
    res = await post_request(f'{CARDINALIS_URL}/api/save_feedback', _logger=logger,
                             json={'task_id': input_task_id, 'text': input_text, 'service': 'telegram'})
    return res.get('response', 0)


async def update_all_chat_photo():
    chats = await get_support_list()
    for i, chat in chats.items():
        photo = await get_profile_photo(chat['chat_id'])
        if photo:
            await sql.update('irobot.subs', f'chat_id={chat["chat_id"]}', photo=photo)


async def new_messages_monitor(logger: Logger, manager: ConnectionManager):
    messages = await sql.execute(
        'SELECT chat_id, message_id, datetime, from_oper AS oper_id, content_type, content '
        'FROM irobot.support_messages WHERE status=%s AND from_oper IS NULL ORDER BY datetime',
        'new', as_dict=True
    )
    for message in messages:
        sql.split_datetime(message)
        await logger.info(f'Get new support message [{message["chat_id"]}] {message["message_id"]}')
        await sql.execute('UPDATE irobot.support_messages SET status= %s WHERE chat_id=%s AND message_id=%s',
                          'sending', message['chat_id'], message['message_id'])
        await manager.broadcast('get_message', message)
        await sql.execute('UPDATE irobot.support_messages SET status= %s WHERE chat_id=%s AND message_id=%s',
                          'sent', message['chat_id'], message['message_id'])
