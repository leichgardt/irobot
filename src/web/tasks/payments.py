from aiologger import Logger

from src.modules import lb, sql
from src.web.utils.notifier import telegram_admin_notify
from src.web.utils.payments import make_payment
from .celery_app import celery_app


@celery_app.task
@celery_app.async_as_sync
async def handle_incomplete_bot_payments(logger: Logger):
    """
    Поиск незавершённых и некорректных платежей
    Попытка провести платёж ещё несколько раз, уведомление администраторов при неудаче
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
                record_id = await make_payment(payment['agrm'], payment['amount'], payment['receipt'])
                if record_id > 0:
                    await sql.upd_payment(payment['hash'], status='success', record_id=record_id)
                    await logger.info(f'Payment monitor: Error Payment made [{payment["chat_id"]}] '
                                      f'ID={payment["payment_id"]}')
                else:
                    await sql.upd_payment(payment['hash'], status='failure')
                    await logger.warning(f'Payment monitor: FAILURE! [{payment["chat_id"]}] ID={payment["id"]}')
                    await telegram_admin_notify(f'[FAILURE]\n\nНевозможно провести платёж', payment["id"], logger)
