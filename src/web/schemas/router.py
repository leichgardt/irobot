from aiologger import Logger
from fastapi import APIRouter


class MyAPIRouter(APIRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = Logger.with_default_handlers()

    def set_logger(self, logger: Logger):
        self.logger = logger
