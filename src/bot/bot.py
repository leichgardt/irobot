import uvloop
import asyncio
from aiogram.utils.executor import start_webhook

from src.text import Texts
from src.bot.layers import bot, dp
from src.lb import lb
from src.sql import sql
from src.utils import config, logger, alogger
from src.utils.logger import logfile

CERTIFICATE = ''
HOST = config['paladin']['maindomain']
WEBHOOK_HOST = f'https://{HOST}/irobot_webhook'
WEBHOOK_PATH = '/'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'  # or ip
WEBAPP_PORT = 5421


async def upd_texts():
    me = await bot.get_me()
    new = Texts.main_menu.format(f'@{me["username"]}')
    Texts.main_menu = Texts.main_menu(new)
    new = Texts.about_us.format(f'@{me["username"]}')
    Texts.about_us = Texts.about_us(new)


async def on_startup(dp):
    try:
        # проверим БД конечного автомата
        await dp.storage.get_data(chat=config['irobot']['me'])
    except Exception:
        raise ConnectionError(f'Can\'t connect to MongoDB: {dp.storage.__dict__["_host"]}')
    sql.logger = alogger
    await upd_texts()
    await lb.login()
    await bot.set_webhook(url=WEBHOOK_URL,
                          certificate=open(CERTIFICATE, 'rb') if CERTIFICATE else None,
                          drop_pending_updates=True)
    logger.info('Bot activated')
    logger.info('See console output in file "{}"'.format(logfile.format(logger.name)))


async def on_shutdown(dp):
    logger.info('Shutting down..')
    await dp.storage.close()
    await bot.delete_webhook()
    await sql.close_pool()
    await dp.storage.wait_closed()
    await alogger.shutdown()
    logger.info('Bye!')


def run_bot():
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    lb.loop = loop
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        # skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        loop=loop
    )
    return loop


if __name__ == '__main__':
    run_bot()
