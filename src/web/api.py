from .telegram_api import telegram_api


async def edit_message(chat_id, message_id, text, parse_mode=None, reply_markup=None):
    try:
        await telegram_api.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=reply_markup)
    except:
        await telegram_api.send_message(chat_id, text, parse_mode, reply_markup=reply_markup)


async def delete_message(chat_id, message_id):
    try:
        await telegram_api.delete_message(chat_id, message_id)
    except:
        pass

