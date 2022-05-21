import asyncio
import os
from datetime import datetime, timedelta
from random import random

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from src.modules import cache_server
from src.web.utils.global_dict import GlobalDict


__all__ = 'SoloWorker',


class SoloWorkerPIDs:
    def __init__(self, key):
        self.key = key
        self._lock = asyncio.Lock()

    async def load_pid_list(self):
        async with self._lock:
            res = await cache_server.get(self.key, list)
        return res or []

    async def update_pid_list(self, pid_list: list):
        async with self._lock:
            return await cache_server.set(self.key, pid_list)

    async def clean_pid_list(self):
        async with self._lock:
            return await cache_server.delete(self.key)


class SoloWorker:
    """
    Класс для распределения задач между процессами/воркерами приложения. Web-приложение Irobot-web работает на
    нескольких воркерах, и, например, чтобы функцию мониторинга платежей выполнял только один процесс, используйте
    декоратор "solo_worker":

    >>> app = FastAPI()
    >>> sw = SoloWorker()
    >>> @app.on_event('start')
    >>> @repeat_every(seconds=5)
    >>> @sw.solo_worker(name='monitor')
    >>> async def monitoring():
    >>>     print('monitoring for every 5 seconds at the only one process of uvicorn processes (workers)')

    Данные о процессах сохраняются в БД "irobot.pids"
    """
    def __init__(self, logger, workers):
        self.pid_controller = SoloWorkerPIDs('solo-worker-pids')
        self.workers_num = workers
        self.logger = logger
        self.pid = os.getpid()
        self.pid_list = []
        self.task_list = []
        self.announcement = set()
        self.running = {}
        self.__closing = False
        self.monitor_flags = GlobalDict('solo-worker-flags')

    async def wait_tasks(self):
        self.logger.info(f'Solo Worker: waiting for tasks [{self.pid}] {self.running}')
        self.__closing = True
        start = datetime.now()
        while True:
            if not any(self.running.values()):
                break
            if start - datetime.now() > timedelta(seconds=30):
                break
            await asyncio.sleep(.1)
        self.logger.info(f'Solo Worker: tasks finished at [{self.pid}]')

    async def update(self):
        if self.workers_num <= 1:
            return
        await asyncio.sleep(random() / 10)
        self.pid_list = await self.pid_controller.load_pid_list()
        if self.pid not in self.pid_list:
            self.pid_list.append(self.pid)
            await self.pid_controller.update_pid_list(self.pid_list)

    async def clean_old_pid_list(self):
        await self.pid_controller.clean_pid_list()
        self.pid_list = []
        self.announcement = set()
        self.running = {}

    def _is_my_task(self, my_task):
        if self.workers_num <= 1:
            return True
        try:
            i = self.pid_list.index(self.pid)
            j = self.task_list.index(my_task)
        except ValueError:
            return False
        else:
            if self.task_list[j] == my_task and j % self.workers_num == i or len(self.pid_list) == 1:
                return True
        return False

    def solo_worker(self, *, task: str, parallel=False, disabled=False):  # factory
        self.task_list.append(task)
        self.monitor_flags[task] = not disabled

        def decorator(func):
            async def wrapper(*args, **kwargs):
                if not self.monitor_flags[task]:
                    return
                if not self.__closing:
                    await self.update()
                    if self._is_my_task(task):
                        if not parallel and self.running.get(task) is True:
                            return
                        self.running[task] = True
                        if task not in self.announcement:
                            self.logger.info(f'Solo worker "{task}" starts in [{self.pid}]')
                            self.announcement.add(task)
                        res = await func(*args, **kwargs)
                        self.running[task] = False
                        return res
            return wrapper
        return decorator
