import aiopg
import asyncio
import psycopg2
import psycopg2.errors

from src.utils import config, is_async_logger


class SQLCore:
    """Ядро асинхронного класса соединения с postgresql. Работает через пул соединений"""
    def __init__(self):
        self._dsn = 'dbname={name} user={user} host={host}'.format(name=config['postgres']['dbname'],
                                                                   user=config['postgres']['dbuser'],
                                                                   host=config['postgres']['dbhost'])
        self.pool = None
        self.pool_min_size = 3
        self.pool_max_size = 20
        # логгер инициализируется в app.py и в src/bot/bot.py отдельно для irobot-web и irobot соответственно
        self.logger = None

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
        self.pool = await aiopg.create_pool(self._dsn, minsize=self.pool_min_size, maxsize=self.pool_max_size)

    async def close_pool(self):
        if self.pool is not None:
            await self.pool.clear()
            self.pool.close()
            await self.pool.wait_closed()
            self.pool.terminate()
            if is_async_logger(self.logger):
                await self.logger.info('PSQL pool closed')
            else:
                self.logger.info('PSQL pool closed')

    async def execute(self, cmd, *args, retrying=False, faults=True):
        res = []
        need_to_retry = not retrying
        if self.pool is None:
            await self.init_pool()
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    if len(args) == 1 and isinstance(args[0], dict):
                        args = args[0]
                    await cur.execute(cmd, args)
                    res = await get_res(cur)
        except psycopg2.errors.AdminShutdown:
            if not retrying:
                return await self.execute(cmd, *args, retrying=True, faults=faults)
        except Exception as e:
            if faults and retrying:
                if is_async_logger(self.logger):
                    await self.logger.warning(f'Error: {e}\nOn cmd: {cmd}\t|\twith args: {args}')
                else:
                    self.logger.warning(f'Error: {e}\nOn cmd: {cmd}\t|\twith args: {args}')
        else:
            need_to_retry = False
        if need_to_retry:
            if isinstance(args, dict):
                args = (args,)
            return await self.execute(cmd, *args, retrying=True)
        return res


async def get_res(cur):
    try:
        ret = await cur.fetchall()
    except psycopg2.ProgrammingError as e:
        if 'no results to fetch' in str(e):
            return None
        else:
            return None
    else:
        ret = [list(line) for line in ret]
        for i in range(len(ret)):
            for y in range(len(ret[i])):
                ret[i][y] = strip_res(ret[i][y])
        return [tuple(line) for line in ret]


def strip_res(val):
    if isinstance(val, str):
        return val.strip()
    elif isinstance(val, (list, set, tuple)):
        val = [strip_res(v) for v in val]
        return val
    elif isinstance(val, dict):
        tmp = {}
        for k, v in val.items():
            tmp.update({k: strip_res(v)})
        return val
    return val
