from aiologger import Logger

from src.modules import sql
from src.web.utils.chat import get_new_support_messages
from src.web.utils.connection_manager import ConnectionManager
from .celery_app import celery_app


@celery_app.task
@celery_app.async_as_sync
async def get_new_subscriber_messages_and_send_to_operators(logger: Logger, manager: ConnectionManager):
    """ Поиск новых сообщений абонентов и их отправка всем операторам """
    messages = await get_new_support_messages()
    for message in messages:
        await logger.info(f'Get new support message [{message["chat_id"]}] {message["message_id"]}')
        await sql.execute('UPDATE irobot.support_messages SET status= %s WHERE chat_id=%s AND message_id=%s',
                          'sending', message['chat_id'], message['message_id'])
        await manager.broadcast('get_message', message)
        await sql.execute('UPDATE irobot.support_messages SET status= %s WHERE chat_id=%s AND message_id=%s',
                          'sent', message['chat_id'], message['message_id'])
