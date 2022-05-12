from aiogram import Bot
from aiologger import Logger


class MyBot(Bot):
    def __init__(self, *args, logger: Logger = None, **kwargs):
        super(MyBot, self).__init__(*args, **kwargs)
        self.logger = logger or Logger.with_default_handlers()
