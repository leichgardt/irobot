from datetime import datetime
from typing import Union, List, Dict

import aiopg
import asyncio
import psycopg2
import psycopg2.errors
import psycopg2.extensions
import ujson
from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler

from config import DB_NAME, DB_USER, DB_HOST


class SQLCore:
    """Ядро асинхронного класса соединения с postgresql. Работает через пул соединений"""
    def __init__(self):
        self._dsn = 'dbname={name} user={user} host={host}'
        self.pool = None
        self.pool_min_size = 3
        self.pool_max_size = 20
        # логгер инициализируется в app.py и в src/bot/bot.py отдельно для irobot-web и irobot соответственно
        self.logger: Logger = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SQLCore, cls).__new__(cls)
        return cls.instance

    def __del__(self):
        try:
            asyncio.run(self.close_pool())
        except:
            pass

    async def init_pool(self):
        if self.pool is not None:  # re-init pool
            await self.close_pool()
        self.pool = await aiopg.create_pool(
            self._dsn.format(name=DB_NAME, user=DB_USER, host=DB_HOST),
            minsize=self.pool_min_size,
            maxsize=self.pool_max_size
        )
        if not self.logger:
            self.logger = Logger.with_default_handlers(name='sql')
            self.logger.add_handler(AsyncStreamHandler())

    async def close_pool(self):
        if self.pool is not None:
            await self.pool.clear()
            self.pool.close()
            await self.pool.wait_closed()
            self.pool.terminate()
            await self.logger.info('PSQL pool closed')

    async def execute(
            self,
            cmd,
            *args,
            retrying=False,
            log_faults=True,
            as_dict=False,
            fetch_one=False
    ) -> Union[dict, List[Dict], List[List]]:
        res = {} if as_dict and fetch_one else []
        need_to_retry = not retrying
        if self.pool is None:
            await self.init_pool()
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    if len(args) == 1 and isinstance(args[0], dict):
                        args = args[0]
                    else:
                        args = [arg if not isinstance(arg, dict) else ujson.dumps(arg) for arg in args]
                    await cur.execute(cmd, args)
                    res = await self.get_res(cur, as_dict, fetch_one)
        except psycopg2.errors.lookup('57P01'):  # AdminShutdown
            if not retrying:
                return await self.execute(cmd, *args, retrying=True, log_faults=log_faults, as_dict=as_dict,
                                          fetch_one=fetch_one)
        except asyncio.exceptions.TimeoutError:
            await self.logger.warning(f'SQL Timed out')
            return res
        except Exception as e:
            if log_faults and retrying and 'duplicate key value violates unique constraint' not in str(e):
                msg = f'SQL exception: {e} CMD: {cmd}' + (f'ARGS: {args}' if args else '')
                await self.logger.exception(msg)
        else:
            need_to_retry = False
        if need_to_retry:
            if isinstance(args, dict):
                args = (args,)
            return await self.execute(cmd, *args, retrying=True, log_faults=log_faults, as_dict=as_dict)
        return res

    async def insert(self, cmd, *args, log_faults=True, as_dict=False):
        res = await self.execute(cmd, *args, log_faults=log_faults, as_dict=as_dict)
        return res[0][0] if res else None

    async def update(self, table, flt, upd_time=None, **kwargs):
        upd = ', '.join([f'{key}= %s' for key in kwargs.keys()])
        dtm = f', {upd_time}=now()' if upd_time else ''
        await self.execute(f'UPDATE {table} SET {upd}{dtm} WHERE {flt}', *kwargs.values())

    async def get_res(self, cur: psycopg2.extensions.cursor, dict_flag, fetch_one):
        try:
            res = await cur.fetchone() if fetch_one else await cur.fetchall()
        except psycopg2.ProgrammingError as e:
            if 'no results to fetch' in str(e):
                if fetch_one and dict_flag:
                    return {}
                else:
                    return []
        else:
            if fetch_one:
                res = list(res)
                for i in range(len(res)):
                    res[i] = self.strip_and_typing_result(res[i])
            else:
                res = [list(line) for line in res]
                for i in range(len(res)):
                    for y in range(len(res[i])):
                        res[i][y] = self.strip_and_typing_result(res[i][y])
                res = [tuple(line) for line in res]
            if dict_flag:
                col_names = [col.name for col in cur.description]
                if fetch_one:
                    res = dict(zip(col_names, res))
                else:
                    res = [dict(zip(col_names, line)) for line in res]
            return res

    def strip_and_typing_result(self, val):
        if 'decimal' in str(type(val)):
            return float(val)
        elif isinstance(val, str):
            return val.strip()
        elif isinstance(val, (list, set, tuple)):
            val = [self.strip_and_typing_result(v) for v in val]
            return val
        elif isinstance(val, dict):
            tmp = {}
            for k, v in val.items():
                tmp.update({k: self.strip_and_typing_result(v)})
            return val
        return val

    @staticmethod
    def split_datetime(
            data: Union[dict, datetime],
            col_name='datetime',
            date_title='date',
            time_title='time',
            timestamp_title='timestamp'
    ):
        if isinstance(data, dict):
            if col_name not in data:
                return None, None, None
            date_ = data[col_name].strftime('%d.%m.%Y')
            time_ = data[col_name].strftime('%H:%M')
            timestamp_ = data[col_name].timestamp()
            data.update({date_title: date_, time_title: time_, timestamp_title: timestamp_})
            data.pop(col_name)
        else:
            date_ = data.strftime('%d.%m.%Y')
            time_ = data.strftime('%H:%M')
            timestamp_ = data.timestamp()
        return date_, time_, timestamp_


if __name__ == '__main__':
    async def main():
        sql = SQLCore()
        res = await sql.execute('SELECT * FROM irobot.subs', as_dict=True, fetch_one=True)
        if res:
            [print(f'{key:18}- {value}') for key, value in res.items()]

    asyncio.run(main())
