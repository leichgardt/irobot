import aiopg
import asyncio
import psycopg2
from src.utils import alogger, config


class SQLCore:
    """Ядро асинхронного класса соединения с postgresql. Работает через пул соединений"""
    def __init__(self):
        self._dsn = 'dbname={name} user={user} host={host}'.format(name=config['postgres']['dbname'],
                                                                   user=config['postgres']['dbuser'],
                                                                   host=config['postgres']['dbhost'])
        self.pool = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SQLCore, cls).__new__(cls)
        return cls.instance

    def __del__(self):
        try:
            asyncio.get_event_loop().run_until_complete(self.close_pool())
        except:
            pass

    async def init_pool(self):
        if self.pool is not None:  # re-init pool
            await self.close_pool()
        self.pool = await aiopg.create_pool(self._dsn, minsize=3, maxsize=20)

    async def close_pool(self):
        if self.pool is not None:
            await alogger.info('Closing pSQL pool...')
            await self.pool.clear()
            self.pool.close()
            await self.pool.wait_closed()
            self.pool.terminate()

    async def execute(self, cmd, *args, retrying=False):
        res = []
        if self.pool is None:
            await self.init_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(args) == 1 and isinstance(args[0], dict):
                    args = args[0]
                try:
                    await cur.execute(cmd, args)
                except Exception as e:
                    if retrying:
                        await alogger.warning(f'Error: {e}\nOn cmd: {cmd}\t|\twith args: {args}')
                    else:
                        await alogger.info(f'Error: {e}\nOn cmd: {cmd}\t|\twith args: {args}')
                    return res
                else:
                    res = await get_res(cur)
        if not res and not retrying and 'select' == cmd[:6].lower():
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
            await alogger.error(f'Fetching error: {e}')
            return None
    else:
        ret = [list(line) for line in ret]
        for i in range(len(ret)):
            for y in range(len(ret[i])):
                if isinstance(ret[i][y], str):
                    ret[i][y] = ret[i][y].strip()
        return [tuple(line) for line in ret]
