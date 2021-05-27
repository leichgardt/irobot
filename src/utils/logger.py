import logging
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.formatters.base import Formatter

f_format = '[%(asctime)s] %(levelname)s  \t%(filename)s(%(lineno)d) - %(funcName)s: %(message)s'
s_format = '%(levelname)s: %(message)s'
logfile = '/var/log/iron/{}.log'


def __init_logger(name, info_file_level=True):
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    s_handler.setFormatter(logging.Formatter(s_format))
    f_handler = logging.FileHandler(logfile.format(name))
    f_handler.setLevel(logging.INFO if info_file_level else logging.WARNING)
    f_handler.setFormatter(logging.Formatter(f_format))

    logger = logging.getLogger(name)
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    logger.setLevel(logging.INFO)
    return logger


def __aio_logger(name):
    s_handler = AsyncStreamHandler(level=logging.INFO, formatter=Formatter(s_format))
    f_handler = AsyncFileHandler(logfile.format(name))
    f_handler.level = logging.INFO
    f_handler.formatter = Formatter(f_format)
    logger = Logger.with_default_handlers(name=name)
    logger.handlers = []
    logger.add_handler(s_handler)
    logger.add_handler(f_handler)
    return logger


logger = __init_logger('irobot')
flogger = __init_logger('irobot-web', False)
alogger = __aio_logger('irobot')


if __name__ == '__main__':
    import asyncio

    async def main():
        logger.info('info')
        logger.warning('warning')
        logger.error('error')
        logger.fatal('fatal')
        await alogger.info('a info')
        await alogger.warning('a warning')
        await alogger.error('a error')
        await alogger.fatal('a fatal')
        await asyncio.sleep(1)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
