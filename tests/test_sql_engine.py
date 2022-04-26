from datetime import datetime

import pytest

from src.modules.sql.core import SQLCore


def test_sql_engine_creation():
    sql1 = SQLCore()
    sql2 = SQLCore()
    assert sql1 is sql2


@pytest.mark.asyncio
async def test_connection_pool_creation():
    sql = SQLCore()
    await sql.init_pool()
    assert sql.pool is not None


@pytest.mark.asyncio
async def test_query_execution():
    async def create_schema(schema_name):
        await sql.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION postgres')

    async def create_table(table_name):
        await sql.execute(f'CREATE TABLE {table_name} (col smallint NOT null)')

    async def insert(table_name):
        await sql.execute(f'INSERT INTO {table_name} (col) VALUES (1) RETURNING col')

    async def select(table_name):
        return await sql.execute(f'SELECT col FROM {table_name}', fetch_one=True, as_dict=True)

    async def drop_schema(schema_name):
        await sql.execute(f'DROP SCHEMA IF EXISTS {schema_name} CASCADE')

    sql = SQLCore()
    ts = datetime.now().timestamp()
    schema = 'tests'
    table = f'tests.test_{int(ts)}'
    await create_schema(schema)
    await create_table(table)
    await insert(table)
    result = await select(table)
    await drop_schema(schema)
    assert result.get('col') == 1
