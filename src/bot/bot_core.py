from aiogram import Bot
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher

from src.parameters import API_TOKEN
from src.utils import config

storage = MongoStorage(host=config['paladin']['cup'], port=27017, db_name='aiogram_fsm')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
