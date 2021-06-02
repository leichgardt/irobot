import logging
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.formatters.base import Formatter

f_format = '[%(asctime)s] %(levelname)-8s %(filename)s(%(lineno)d) - %(funcName)s: %(message)s'
s_format = '%(levelname)-9s %(message)s'
logfile = '/var/log/iron/{}.log'


def init_logger(name, info_file_level=True):
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    s_handler.setFormatter(logging.Formatter(s_format))
    f_handler = logging.FileHandler(logfile.format(name))
    f_handler.setLevel(logging.INFO if info_file_level else logging.WARNING)
    f_handler.setFormatter(logging.Formatter(f_format))

    logger = logging.getLogger(name)
    logger.handlers = []
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    logger.setLevel(logging.INFO)
    return logger


def aio_logger(name, loop=None):
    s_handler = AsyncStreamHandler(level=logging.INFO, formatter=Formatter(s_format))
    f_handler = AsyncFileHandler(logfile.format(name))
    f_handler.level = logging.INFO
    f_handler.formatter = Formatter(f_format)
    logger = Logger(name=name, loop=loop)
    logger.add_handler(s_handler)
    logger.add_handler(f_handler)
    logger.level = logging.INFO
    return logger


logger = init_logger('irobot')
alogger = aio_logger('irobot')
