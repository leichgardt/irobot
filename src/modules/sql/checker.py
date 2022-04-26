import importlib

from config import PID_TABLE, PID_DEBUG_TABLE
from src.modules.sql.core import SQLCore
from src.modules.sql.creating import schema_irobot


SCHEMA = 'irobot'

TABLE_LIST = (
    'accounts',
    'feedback',
    'mailing',
    'operators',
    'payments',
    'subs',
    'support',
    'support_messages',
    'support_oper_history',
    'tokens',
    PID_TABLE,
    PID_DEBUG_TABLE
)


class CheckerSQL:
    def __init__(self, api_engine: SQLCore):
        self.api = api_engine

    async def check_db_ready(self):
        await self.check_schema_exists()
        await self.check_all_tables_exists()
        await self.add_extension()

    async def check_schema_exists(self):
        res = await self.get_schema()
        if not res:
            await self.create_schema()

    async def get_schema(self):
        res = await self.api.execute('SELECT schema_name FROM information_schema.schemata WHERE schema_name=%s', SCHEMA)
        return res[0][0] if res else None

    async def create_schema(self):
        print(f'creating schema "{SCHEMA}"')
        await self.api.execute(schema_irobot.cmd)

    async def check_all_tables_exists(self):
        tables = await self.get_table_list()
        for table in TABLE_LIST:
            if table not in tables:
                await self.create_table(table)

    async def get_table_list(self):
        res = await self.api.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = %s', SCHEMA)
        return [r[0] for r in res]

    async def create_table(self, table):
        print(f'creating table "{table}"')
        if table in (PID_TABLE, PID_DEBUG_TABLE):
            i = self.import_table_module('processes')
            await self.api.execute(i.cmd.format(name=table))
        else:
            i = self.import_table_module(table)
            await self.api.execute(i.cmd)

    @staticmethod
    def import_table_module(table):
        return importlib.import_module(f'src.modules.sql.creating.{table}')

    async def add_extension(self):
        await self.api.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')


if __name__ == '__main__':
    import asyncio

    sql = SQLCore()
    ch = CheckerSQL(sql)

    asyncio.run(ch.check_db_ready())
