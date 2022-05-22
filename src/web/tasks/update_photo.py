from src.modules import sql
from src.web.utils.chat import get_support_list
from src.web.utils.telegram_api import get_profile_photo
from .celery_app import celery_app


@celery_app.task
@celery_app.async_as_sync
async def update_subscriber_chat_photos():
    """ Обновить URL на telegram-аватарки абонентов """
    chats = await get_support_list()
    for i, chat in chats.items():
        photo = await get_profile_photo(chat['chat_id'])
        if photo:
            await sql.update('irobot.subs', f'chat_id={chat["chat_id"]}', photo=photo)
