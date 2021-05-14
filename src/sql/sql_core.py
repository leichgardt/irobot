import aiopg
import psycopg2
from src.utils import logger, config


class SQLCore:
    def __init__(self):
        host = config['postgres']['dbhost']
        name = config['postgres']['dbname']
        user = config['postgres']['dbuser']
        self._dsn = f'dbname={name} user={user} host={host}'
        self.pool = None
        self.logger = logger

    def __del__(self):
        try:
            self.close_pool()
        except:
            pass

    async def init_pool(self):
        self.pool = await aiopg.create_pool(self._dsn, minsize=3, maxsize=20)

    def close_pool(self):
        if self.pool is not None:
            self.pool.terminate()

    async def execute(self, cmd, *args, retrying=False):
        res = []
        if self.pool is None:
            await self.init_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                self.logger.debug(f'cmd: {cmd}\t###\targs: {args}')
                if len(args) == 1 and isinstance(args[0], dict):
                    args = args[0]
                try:
                    await cur.execute(cmd, args)
                except Exception as e:
                    text = f'Error: {e}\nOn cmd: {cmd}\t|\twith args: {args}'
                    if retrying:
                        self.logger.warning(text)
                    else:
                        self.logger.info(text)
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
            logger.error(f'Fetching error: {e}')
            return None
    else:
        ret = [list(line) for line in ret]
        for i in range(len(ret)):
            for y in range(len(ret[i])):
                if isinstance(ret[i][y], str):
                    ret[i][y] = ret[i][y].strip()
        return [tuple(line) for line in ret]
