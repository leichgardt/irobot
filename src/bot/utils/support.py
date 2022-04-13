from datetime import datetime

from aiogram import types

from src.modules import sql
from src.utils import logger


async def create_support(chat_id: int) -> int:
    chat = await sql.execute('SELECT support_id FROM irobot.support WHERE chat_id=%s AND closed IS null', chat_id,
                             fetch_one=True)
    if chat:
        return chat[0]
    else:
        return await sql.insert('INSERT INTO irobot.support (chat_id) VALUES (%s) RETURNING support_id', chat_id)


async def close_support(support_id: int):
    await sql.execute('UPDATE irobot.support SET closed=now() WHERE support_id=%s', support_id)


async def add_support_message(message: types.Message):
    if message.content_type == 'text':
        data = {'text': message.text}
    elif message.content_type == 'document':
        data = {'file_id': message.document.file_id, 'mime_type': message.document.mime_type}
    elif message.content_type == 'photo':
        data = {'file_id': message.photo[-1].file_id}
    elif message.content_type == 'sticker':
        data = {'file_id': message.sticker.file_id}
    elif message.content_type == 'voice':
        data = {'file_id': message.voice.file_id}
    elif message.content_type == 'video':
        data = {'file_id': message.video.file_id, 'mime_type': message.video.mime_type}
    elif message.content_type == 'video_note':
        data = {'file_id': message.video_note.file_id}
    elif message.content_type == 'audio':
        data = {'file_id': message.audio.file_id, 'mime_type': message.audio.mime_type}
    else:
        await logger.warning(f'Unhandled support message content type: {message} [{message.chat.id}]')
        return
    data = {'caption': message.caption, **data} if 'caption' in message else data
    await update_support_datetime(message.chat.id)
    await add_support_message_to_db(message.chat.id, message.message_id, message.content_type, data, status='new')


async def update_support_datetime(chat_id):
    await sql.execute('''
    UPDATE irobot.support SET closed=null WHERE support_id=(
        SELECT support_id FROM irobot.support 
            WHERE (chat_id=%(chat_id)s AND closed IS null) OR
                closed=(SELECT MAX(closed) 
                            FROM irobot.support 
                        WHERE chat_id=%(chat_id)s)
            ORDER BY closed DESC LIMIT 1)''', {'chat_id': chat_id})


async def add_support_message_to_db(
        chat_id: int,
        message_id: int,
        message_type: str,
        message_data: dict,
        oper_id: int = None,
        read: bool = False,
        status: str = None
) -> datetime:
    return await sql.insert(
        'INSERT INTO irobot.support_messages (chat_id, message_id, content_type, content, from_oper, read, status) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING datetime',
        chat_id, message_id, message_type, message_data, oper_id, read, status
    )


async def add_system_support_message(chat_id: int, message_id: int, text: str):
    await add_support_message_to_db(chat_id, message_id, 'text', {'text': text}, oper_id=0, read=True, status=None)


async def rate_support(support_id: int, rating: int):
    await sql.execute('UPDATE irobot.support SET rating= %s WHERE support_id=%s', rating, support_id)
