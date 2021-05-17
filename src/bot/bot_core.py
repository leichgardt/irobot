from aiogram import Bot
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher

from src.utils import config

API_TOKEN = config['tesseract']['token-iro-mega-bot']

storage = MongoStorage(host='localhost', port=27017, db_name='aiogram_fsm')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

