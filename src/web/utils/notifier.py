from config import TELEGRAM_NOTIFY_BOT_URL, TELEGRAM_TEST_CHAT_ID
from src.utils import post_request
from src.web.utils.telegram_api import send_message


async def telegram_admin_notify(message, payment_id, logger):
    text = f'Irobot Payment Monitor\n\n{message}\n\nPayment ID = {payment_id}'
    if TELEGRAM_NOTIFY_BOT_URL:
        await post_request(TELEGRAM_NOTIFY_BOT_URL, json={'chat_id': TELEGRAM_TEST_CHAT_ID, 'text': text},
                           logger=logger)
    await send_message(TELEGRAM_TEST_CHAT_ID, text)
