from aiologger import Logger
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates


class AdminAPIRouter(APIRouter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = Logger.with_default_handlers()


router = AdminAPIRouter(prefix='/admin')
templates = Jinja2Templates(directory='templates')
