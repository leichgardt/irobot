from aiologger import Logger

from src.modules import lb, sql
from src.web.utils.cardinalis import send_feedback_to_cardinalis
from src.web.utils.chat import get_support_list
from src.web.utils.connection_manager import ConnectionManager
from src.web.utils.notifier import telegram_admin_notify
from src.web.utils.payment_tryer import try_make_payment
from src.web.utils.telegram_api import get_profile_photo


__all__ = ('auto_feedback_monitor', 'auto_payment_monitor', 'chat_photo_update_monitor', 'new_messages_monitor')


async def auto_payment_monitor(logger: Logger):
    """
    Поиск незавершённых и некорректных платежей
    Монитор пытается провести платёж ещё несколько раз, и при неудаче - уведомляет администратора
    """
    payments = await sql.find_processing_payments()
    if payments:
        for payment in payments:
            await logger.info(f'Payment monitor catch the payment [{payment["chat_id"]}] {payment["id"]=} '
                              f'{payment["status"]=}')
            if payment['status'] == 'processing':
                record_id = await lb.new_payment(payment['agrm'], payment['amount'], payment['receipt'])
                if record_id:
                    await sql.upd_payment(payment['hash'], status='success', record_id=record_id)
                    await logger.info(f'Payment monitor: [{payment["chat_id"]}] {payment["id"]=} SUCCESS')
                else:
                    await sql.upd_payment(payment['hash'], status='error')
                    await logger.warning(f'Payment monitor: [{payment["chat_id"]}] {payment["id"]=} ERROR')

            elif payment['status'] == 'success':
                lb_payment = await lb.get_payment(payment['record_id'])
                if lb_payment and payment['receipt'] in lb_payment.pay.receipt:
                    await sql.upd_payment(payment['hash'], status='completed')
                    await logger.info(f'Payment monitor: [{payment["chat_id"]}] {payment["id"]=} COMPLETED')
                else:
                    await sql.upd_payment(payment['hash'], status='warning')
                    await logger.warning(f'Payment monitor: [{payment["chat_id"]}] {payment["id"]=} WARNING')
                    await telegram_admin_notify(f'[WARNING]\n\nМонитор не может проверить платёж', payment["id"],
                                                logger)

            elif payment['status'] == 'error':
                # обработка платежа, у которого не прошёл платёж в биллинг
                record_id = await try_make_payment(payment['agrm'], payment['amount'], payment['receipt'])
                if record_id > 0:
                    await sql.upd_payment(payment['hash'], status='success', record_id=record_id)
                    await logger.info(f'Payment monitor: Error Payment made [{payment["chat_id"]}] '
                                      f'ID={payment["payment_id"]}')
                else:
                    await sql.upd_payment(payment['hash'], status='failure')
                    await logger.warning(f'Payment monitor: FAILURE! [{payment["chat_id"]}] ID={payment["id"]}')
                    await telegram_admin_notify(f'[FAILURE]\n\nНевозможно провести платёж', payment["id"], logger)


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
