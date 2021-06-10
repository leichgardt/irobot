import os
import asyncio
import psutil

from src.sql import sql
from src.utils import alogger as logger


class SoloWorker:
    def __init__(self):
        self.pid = os.getpid()
        self.pid_list = {}
        self.permission = {}
        self.announcement = set()

    async def update(self):
        res = await sql.get_pid_list()
        if res:
            self.pid_list = {}
            for pid, tasks in res:
                self.pid_list.update({pid: tasks})
            self.pid_list = dict(sorted(self.pid_list.items(), key=lambda item: len(item[1])))
        else:
            self.clean_params()

    def clean_params(self):
        self.pid_list = {}
        self.permission = {}
        self.announcement = set()

    async def clean_old_pid_list(self):
        await sql.del_pid_list()
        self.clean_params()

    async def get_permission(self, task):
        await asyncio.sleep(2)
        await self.update()
        if self.pid not in self.pid_list:
            await sql.add_pid(self.pid)
        await asyncio.sleep(5)
        await self.update()
        if self.pid_list:
            for tasks in self.pid_list.values():
                if task in tasks:
                    return False
            if list(self.pid_list.keys())[0] == self.pid:
                return True
        return False

    async def check_pid_list(self):
        await self.update()
        if self.pid not in self.pid_list:
            self.clean_params()
            return
        zombie = [data.info['pid'] for data in psutil.process_iter(['pid', 'status'])
                  if data.info['pid'] in self.pid_list and data.info['status'] == 'zombie']
        if zombie and set(zombie) & set(self.pid_list):
            await sql.del_pid(zombie[0])
            self.clean_params()

    def solo_worker(self, *, name: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                await self.check_pid_list()
                if self.permission.get(name) is None:
                    self.permission.update({name: await self.get_permission(name)})
                if self.permission.get(name):
                    if name not in self.announcement:
                        await logger.info(f'Solo worker "{name}" starts in [{os.getpid()}]')
                        self.announcement.add(name)
                        await sql.upd_pid(self.pid, [name])
                    return await func(*args, **kwargs)
            return wrapper
        return decorator
