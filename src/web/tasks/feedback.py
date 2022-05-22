from aiologger import Logger

from src.modules import sql
from src.web.utils.cardinalis import send_feedback_to_cardinalis
from .celery_app import celery_app


@celery_app.task
@celery_app.async_as_sync
async def handle_feedback_tasks(logger: Logger):
    """
    Мониторинг feedback-заявок Userside

    Если найден новый Feedback (статус "new"/"sending"), то он отправляется в систему сбора статистики "Cardinalis".
    При успехе Feedback переходит в статус "sent".
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
