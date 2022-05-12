import logging
from typing import Dict

from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.handlers.files import AsyncFileHandler
from aiologger.formatters.base import Formatter


__all__ = ('AIOLogger', 'logdir', 'logfile')


f_format = '[%(asctime)s] %(levelname)-8s %(filename)s(%(lineno)d) - %(funcName)s: %(message)s'
s_format1 = '[%(asctime)s] %(levelname)-9s %(message)s'
s_format2 = '%(levelname)-9s %(message)s'
logdir = '/var/log/'
logfile = '{}.log'


class AIOLogger(Logger):
    _instances: Dict[str, Logger] = {}

    def __init__(self, *, name='aiologger', level=logging.INFO):
        super(AIOLogger, self).__init__(name=name, level=level)
        s_handler = AsyncStreamHandler(level=level, formatter=Formatter(s_format1))
        f_handler = AsyncFileHandler(logdir + logfile.format(name))
        f_handler.level = level
        f_handler.formatter = Formatter(f_format)
        self.add_handler(s_handler)
        self.add_handler(f_handler)
        self.level = level

    def __new__(cls, *, name='aiologger', level=logging.NOTSET):
        if name not in cls._instances:
            cls._instances[name] = super(AIOLogger, cls).__new__(cls)
        return cls._instances[name]
