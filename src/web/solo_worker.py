import os

from src.sql import sql


class SoloWorker:
    """
    Класс для распределения задач между процессами/воркерами. Web-приложение Irobot-web работает на нескольких воркерах,
    и, например, чтобы функцию мониторинга платежей выполнял только один процесс, используйте декоратор:
    >>> sw = SoloWorker()
    >>> @app.on_event('start')
    >>> @repeat_every(seconds=5)
    >>> @sw.solo_worker(name='monitor')
    >>> async def monitor():
    >>>     print('monitoring every 5 seconds at only one process of uvicorn processes')
    Данные о процессах сохраняются в БД "irobot.pids"
    """
    def __init__(self, logger, workers):
        self.workers = workers
        self.logger = logger
        self.pid = os.getpid()
        self.pid_list = []
        self.task_list = []
        self.announcement = set()

    async def update(self):
        res = await sql.get_pid_list()
        self.pid_list = [row[0] for row in res] if res else res
        if self.pid not in self.pid_list:
            await sql.add_pid(self.pid)

    async def clean_old_pid_list(self):
        await sql.del_pid_list()
        self.pid_list = []
        self.task_list = []
        self.announcement = set()

    def _is_my_task(self, my_task):
        for i, pid in enumerate(self.pid_list):
            if pid == self.pid:
                for j, task in enumerate(self.task_list):
                    if task == my_task and j % self.workers == i:
                        return True
        return False

    def solo_worker(self, *, task: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if task not in self.task_list:
                    self.task_list.append(task)
                await self.update()
                if self._is_my_task(task):
                    if task not in self.announcement:
                        self.logger.info(f'Solo worker "{task}" starts in [{self.pid}]')
                        self.announcement.add(task)
                    return await func(*args, **kwargs)
            return wrapper
        return decorator
