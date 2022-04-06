from aiogram import Bot
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher

from src.parameters import API_TOKEN, MONGO_DB_HOST, MONGO_DB_PORT, MONGO_DB_NAME


storage = MongoStorage(host=MONGO_DB_HOST, port=MONGO_DB_PORT, db_name=MONGO_DB_NAME)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
