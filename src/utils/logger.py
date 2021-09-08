import logging
import os

from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.formatters.base import Formatter

f_format = '[%(asctime)s] %(levelname)-8s %(filename)s(%(lineno)d) - %(funcName)s: %(message)s'
s_format1 = '[%(asctime)s] %(levelname)-9s %(message)s'
s_format2 = '%(levelname)-9s %(message)s'
logdir = '/var/log/iron/'
logfile = '{}.log'


def aio_logger(name, loop=None):
    if not os.path.exists(logdir):
        os.makedirs(logdir, mode=0o775)

    s_handler = AsyncStreamHandler(level=logging.INFO, formatter=Formatter(s_format1))
    f_handler = AsyncFileHandler(logdir + logfile.format(name))
    f_handler.level = logging.WARNING
    f_handler.formatter = Formatter(f_format)
    logger = Logger(name=name, loop=loop)
    logger.add_handler(s_handler)
    logger.add_handler(f_handler)
    logger.level = logging.INFO
    return logger


alogger = aio_logger('irobot')
