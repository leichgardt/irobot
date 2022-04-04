from src.bot.api.keyboard import KeyboardButton


__all__ = ('get_support_kb',)


def get_support_kb(client_chat_id):
    return [
        KeyboardButton('Принять запрос', callback_data=f'get-support-line-{client_chat_id}')
    ]
