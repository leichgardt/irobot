from aiogram import types

from src.modules import sql
from src.parameters import HOST_URL
from src.utils import logger, post_request


async def create_support_chat(chat_id):
    chat = await sql.execute('select chat_id from irobot.support_chats where chat_id=%s', chat_id, fetch_one=True)
    if chat:
        await sql.update('irobot.support_chats', f'chat_id={chat_id}', support_mode=True, datetime='now()', read=False)
    else:
        await sql.insert('insert into irobot.support_chats (chat_id) VALUES (%s)', chat_id)


async def save_dialog_message(message: types.Message):
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
    await sql.add_support_message(message.chat.id, message.message_id, message.content_type, data)


async def broadcast_support_message(chat_id, message_id):
    await post_request(f'{HOST_URL}/admin/api/new_message', json={'chat_id': chat_id, 'message_id': message_id})
