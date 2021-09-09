import aiopg
import asyncio
import psycopg2
import psycopg2.errors
import psycopg2.extensions
import ujson

from src.utils import config


class SQLCore:
    """Ядро асинхронного класса соединения с postgresql. Работает через пул соединений"""
    def __init__(self):
        self._dsn = 'dbname={name} user={user} host={host}'
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
        self.pool = await aiopg.create_pool(self._dsn.format(name=config['postgres']['dbname'],
                                                             user=config['postgres']['dbuser'],
                                                             host=config['postgres']['dbhost']),
                                            minsize=self.pool_min_size,
                                            maxsize=self.pool_max_size)

    async def close_pool(self):
        if self.pool is not None:
            await self.pool.clear()
            self.pool.close()
            await self.pool.wait_closed()
            self.pool.terminate()
            await self.logger.info('PSQL pool closed')

    async def execute(self, cmd, *args, retrying=False, log_faults=True, as_dict=False):
        res = []
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
                    res = await get_res(cur, as_dict)
        except psycopg2.errors.AdminShutdown:
            if not retrying:
                return await self.execute(cmd, *args, retrying=True, log_faults=log_faults)
        except Exception as e:
            if log_faults and retrying and 'duplicate key value violates unique constraint' not in e:
                msg = f'SQL exception: {e}CMD: {cmd}' + f'\nARGS: {args}' if args else ''
                await self.logger.warning(msg)
        else:
            need_to_retry = False
        if need_to_retry:
            if isinstance(args, dict):
                args = (args,)
            return await self.execute(cmd, *args, retrying=True)
        return res


async def get_res(cur, dict_flag):
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
                ret[i][y] = strip_and_typing_res(ret[i][y])
        res = [tuple(line) for line in ret]
        if dict_flag:
            col_names = [col.name for col in cur.description]
            res = [dict(zip(col_names, line)) for line in res]
        return res


def strip_and_typing_res(val):
    if 'decimal' in str(type(val)):
        return float(val)
    elif isinstance(val, str):
        return val.strip()
    elif isinstance(val, (list, set, tuple)):
        val = [strip_and_typing_res(v) for v in val]
        return val
    elif isinstance(val, dict):
        tmp = {}
        for k, v in val.items():
            tmp.update({k: strip_and_typing_res(v)})
        return val
    return val


if __name__ == '__main__':
    from src.utils import alogger

    async def main():
        sql = SQLCore()
        sql.logger = alogger
        res = await sql.execute('SELECT * FROM irobot.subs WHERE chat_id=%s', config['irobot']['me'], as_dict=True)
        if res:
            [print(f'{column:20}: {value}') for row in res for column, value in row.items()]

    asyncio.run(main())
