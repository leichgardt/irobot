from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher import Dispatcher

from config import BOT_TOKEN, DEBUG, MONGO_DB_HOST, MONGO_DB_PORT, MONGO_DB_NAME
from src.bot.schemas.bot import MyBot
from src.utils import AIOLogger


if DEBUG:
    storage = MemoryStorage()
else:
    storage = MongoStorage(host=MONGO_DB_HOST, port=MONGO_DB_PORT, db_name=MONGO_DB_NAME)

bot = MyBot(token=BOT_TOKEN, logger=AIOLogger(name='irobot'))
dp = Dispatcher(bot, storage=storage)
