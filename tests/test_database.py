"""
Таблицы создаются при запуске бота или веб-приложения, если их нет в модуле `src.modules.sql.checker`
"""

import pytest

from src.modules.sql.checker import SQLCore, CheckerSQL, SCHEMA, TABLE_LIST


@pytest.mark.asyncio
async def test_database_schema():
    sql = SQLCore()
    checker = CheckerSQL(sql)
    schema = await checker.get_schema()
    assert schema == SCHEMA


@pytest.mark.asyncio
async def test_database_tables():
    sql = SQLCore()
    checker = CheckerSQL(sql)
    tables = await checker.get_table_list()
    for table in tables:
        assert table in TABLE_LIST
