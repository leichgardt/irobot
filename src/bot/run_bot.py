__author__ = 'leichgardt'

import asyncio

import uvloop
from aiogram.utils.executor import start_webhook

from src.bot import bot, dp
from config import DEBUG, TELEGRAM_TEST_CHAT_ID, BOT_WEBHOOK_URL, BOT_PORT
from src.modules import lb, sql, Texts
from src.modules.sql.checker import CheckerSQL
from src.utils import logfile, logdir

CERTIFICATE = ''
WEBHOOK_PATH = '/'
WEBHOOK_URL = f'{BOT_WEBHOOK_URL}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = BOT_PORT


async def upd_texts():
    me = await bot.get_me()
    Texts.me = Texts.me(Texts.me.format(name=me['username']))
    Texts.main_menu = Texts.main_menu(Texts.main_menu.format(f'@{me["username"]}'))
    Texts.about_us = Texts.about_us(Texts.about_us.format(f'@{me["username"]}'))


async def check_mongo(dp):
    try:
        # проверим БД конечного автомата
        await dp.storage.get_data(chat=TELEGRAM_TEST_CHAT_ID)
    except Exception:
        raise ConnectionError(f'Can\'t connect to MongoDB: {dp.storage.__dict__["_host"]}')


async def check_postgres():
    sql_checker = CheckerSQL(sql)
    await sql_checker.check_db_ready()


async def on_startup(dp):
    sql.logger = bot.logger
    await check_postgres()
    await check_mongo(dp)
    await upd_texts()
    await lb.login()
    await bot.set_webhook(url=WEBHOOK_URL,
                          certificate=open(CERTIFICATE, 'rb') if CERTIFICATE else None,
                          drop_pending_updates=True)
    await bot.logger.info(f'Bot activated. Look at the console output in file '
                          f'"{logdir + logfile.format(bot.logger.name)}"')


async def on_shutdown(dp):
    await bot.logger.info('Shutting down..')
    await dp.storage.close()
    await bot.delete_webhook()
    await sql.close_pool()
    await dp.storage.wait_closed()
    await bot.logger.shutdown()
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
        skip_updates=DEBUG,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        loop=loop
    )
    return loop


if __name__ == '__main__':
    run_bot()
