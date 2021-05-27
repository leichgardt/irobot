import asyncio
import psycopg2
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from src.utils import config, flogger as logger


class SQLCore:
    def __init__(self):
        self._db = config['postgres']['dbname']
        self._host = config['postgres']['dbhost']
        self._user = config['postgres']['dbuser']
        self._pwd = config['postgres']['dbpasswd']
        self.con = self._init_connection()
        self._cur = self.con.cursor()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.loop = None

    def _init_connection(self):
        return psycopg2.connect(database=self._db,
                                host=self._host,
                                user=self._user,
                                password=self._pwd)

    def __enter__(self):
        if self.con.closed:
            logger.fatal('SQL database connection closed')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        try:
            self.con.close()
        except Exception:
            pass

    def execute(self, cmd: str, *args, retrying=False, history=False):
        cmd = cmd.replace('"', '\'')
        if not history:
            logger.debug(f'{cmd}' + f'\nargs: {args}' if args else '')
        try:
            self._cur.execute(cmd, args)
        except psycopg2.InterfaceError:
            if not retrying:
                self.con = self._init_connection()
                self._cur = self.con.cursor()
                return self.execute(cmd, *args, retrying=True)
            else:
                logger.error(f'\tcmd: {cmd}\t(args: {args})')
                return None
        except Exception as e:
            logger.error(f'{e}\tcmd: {cmd}\t(args: {args})')
            return None
        else:
            self.con.commit()
            rez = self._get_rez()
            if not history:
                self.add_to_history(cmd, *args)
            return rez

    def _get_rez(self):
        try:
            rez = self._cur.fetchall()
        except psycopg2.ProgrammingError as e:
            if 'no results to fetch' in str(e):
                return None
            else:
                logger.error(f'Getting rez error: {e}')
                return None
        else:
            for i in range(len(rez)):
                rez[i] = list(rez[i])
                for j in range(len(rez[i])):
                    if isinstance(rez[i][j], str):
                        rez[i][j] = rez[i][j].strip()
                rez[i] = tuple(rez[i])
            return rez

    def add_to_history(self, cmd, *args):
        if cmd[:6].lower() != 'select':
            self.execute('INSERT INTO support.journal (cmd, args) VALUES (%s, %s)', cmd, str(args), history=True)

    async def aexecute(self, *args, **kwargs):
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        elif self.loop.is_closed():
            self.loop = asyncio.get_event_loop()
        logger.debug(f'LB request: {args} & {kwargs}')
        return await self.loop.run_in_executor(self.executor, partial(self.execute, *args, **kwargs))


def expand_dict(data):
    keys = list(data.keys())
    keys = ', '.join(keys)
    values = list(data.values())
    pointers = ['%s' for _ in values]
    pointers = ', '.join(pointers)
    return keys, values, pointers


def fold_dict(data):
    keys = [f'{key}=%s' for key in data.keys()]
    values = [value for value in data.values()]
    return ', '.join(keys), values
