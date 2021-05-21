import logging
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.formatters.base import Formatter

f_format = '[%(asctime)s] %(levelname)s \tin %(filename)s: %(funcName)s(%(lineno)d): %(message)s'
s_format = '[%(asctime)s] %(levelname)s: %(message)s'
logfile = '/var/log/iron/mega_bot.log'
project = 'iro-mega-bot'


def __init_logger(name):
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    s_handler.setFormatter(logging.Formatter(s_format))
    f_handler = logging.FileHandler(logfile)
    f_handler.setLevel(logging.WARNING)
    f_handler.setFormatter(logging.Formatter(f_format))

    logger = logging.getLogger(name)
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    logger.setLevel(logging.INFO)
    return logger


def __aio_logger(name):
    s_handler = AsyncStreamHandler(level=logging.INFO, formatter=Formatter(s_format))
    f_handler = AsyncFileHandler(logfile)
    f_handler.level = logging.WARNING
    f_handler.formatter = Formatter(f_format)
    logger = Logger.with_default_handlers(name=name)
    logger.handlers = []
    logger.add_handler(s_handler)
    logger.add_handler(f_handler)
    return logger


logger = __init_logger(project)
alogger = __aio_logger(project)
