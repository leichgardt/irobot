from aiogram.utils.executor import start_webhook

from src.bot.layers import bot, dp
from src.lb.lb_suds import lb
from src.utils import logger, alogger, config
from src.utils.logger import logfile

CERTIFICATE = ''
HOST = config['paladin']['userside']  # api.userside.com
WEBHOOK_HOST = f'https://{HOST}/irobot'
WEBHOOK_PATH = '/'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'  # or ip
WEBAPP_PORT = 5421


async def on_startup(dp):
    lb.login()
    await bot.set_webhook(url=WEBHOOK_URL,
                          certificate=open(CERTIFICATE, 'rb') if CERTIFICATE else None,
                          drop_pending_updates=True)


async def on_shutdown(dp):
    logger.info('Shutting down..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logger.info('Bye!')
    await alogger.shutdown()


def run_bot():
    logger.info('Bot activated')
    logger.info(f'See console output in file "{logfile}"')
    import uvloop
    import asyncio
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
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


if __name__ == '__main__':
    run_bot()
