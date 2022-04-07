__author__ = 'leichgardt'

import asyncio

import uvloop
from aiogram.utils.executor import start_webhook

from src.bot import bot, dp
from parameters import TELEGRAM_TEST_CHAT_ID, BOT_WEBHOOK_URL
from src.modules import lb, sql, Texts
from src.utils import logger, logfile, logdir

CERTIFICATE = ''
WEBHOOK_PATH = '/'
WEBHOOK_URL = f'{BOT_WEBHOOK_URL}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 5421


async def upd_texts():
    me = await bot.get_me()
    Texts.me = Texts.me(Texts.me.format(name=me['username']))
    Texts.main_menu = Texts.main_menu(Texts.main_menu.format(f'@{me["username"]}'))
    Texts.about_us = Texts.about_us(Texts.about_us.format(f'@{me["username"]}'))


async def on_startup(dp):
    try:
        # проверим БД конечного автомата
        await dp.storage.get_data(chat=TELEGRAM_TEST_CHAT_ID)
    except Exception:
        raise ConnectionError(f'Can\'t connect to MongoDB: {dp.storage.__dict__["_host"]}')
    sql.logger = logger
    await upd_texts()
    await lb.login()
    await bot.set_webhook(url=WEBHOOK_URL,
                          certificate=open(CERTIFICATE, 'rb') if CERTIFICATE else None,
                          drop_pending_updates=True)
    await logger.info(f'Bot activated. Look at the console output in file "{logdir + logfile.format(logger.name)}"')


async def on_shutdown(dp):
    await logger.info('Shutting down..')
    await dp.storage.close()
    await bot.delete_webhook()
    await sql.close_pool()
    await dp.storage.wait_closed()
    await logger.shutdown()
    print('Bye!')


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
