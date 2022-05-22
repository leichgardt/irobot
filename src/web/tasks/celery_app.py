import asyncio
from functools import wraps

from celery import Celery

from config import REDIS_URL


class AsyncCelery(Celery):
    """
    Чтобы запустить celery worker, выполните команду в терминале
    > celery -A src.web.tasks.celery_worker worker --loglevel=INFO
    """

    @staticmethod
    def async_as_sync(func):
        """ Вызывать async функцию без ``await``! """
        @wraps(func)
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(func(*args, **kwargs))

        return wrapper


celery_app = AsyncCelery('tasks', broker=f'{REDIS_URL}/1')
