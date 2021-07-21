import os
import asyncio

from src.sql import sql


class SoloWorker:
    """
    Класс для распределения задач между процессами/воркерами. Web-приложение Irobot-web работает на нескольких воркерах,
    и, например, чтобы функцию мониторинга платежей выполнял только один процесс, используйте декоратор "solo_worker":
    >>> sw = SoloWorker()
    >>> @app.on_event('start')
    >>> @repeat_every(seconds=5)
    >>> @sw.solo_worker(name='monitor')
    >>> async def monitor():
    >>>     print('monitoring every 5 seconds at only one process of uvicorn processes')
    Данные о процессах сохраняются в БД "irobot.pids"
    """
    def __init__(self, logger, workers):
        self.workers_num = workers
        self.logger = logger
        self.pid = os.getpid()
        self.pid_list = []
        self.task_list = []
        self.announcement = set()
        self.running = {}
        self.block = False

    async def close_tasks(self):
        self.block = True
        while True in self.running.values():
            await asyncio.sleep(.1)

    async def update(self):
        res = await sql.get_pid_list()
        self.pid_list = [row[0] for row in res] if res else []
        if self.pid not in self.pid_list:
            await sql.add_pid(self.pid)

    async def clean_old_pid_list(self):
        await sql.del_pid_list()
        self.pid_list = []
        self.announcement = set()
        self.running = {}

    def _is_my_task(self, my_task):
        try:
            i = self.pid_list.index(self.pid)
            j = self.task_list.index(my_task)
        except ValueError:
            return False
        else:
            if self.task_list[j] == my_task and j % self.workers_num == i:
                return True
        return False

    def solo_worker(self, *, task: str):  # factory
        self.task_list.append(task)

        def decorator(func):
            async def wrapper(*args, **kwargs):
                if not self.block:
                    await self.update()
                    if self._is_my_task(task):
                        self.running[task] = True
                        if task not in self.announcement:
                            self.logger.info(f'Solo worker "{task}" starts in [{self.pid}]')
                            self.announcement.add(task)
                        res = await func(*args, **kwargs)
                        self.running[task] = False
                        return res
            return wrapper
        return decorator
