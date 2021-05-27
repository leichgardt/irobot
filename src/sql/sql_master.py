try:
    from .sql_core import SQLCore
except ImportError:
    from sql_core import SQLCore


class SQLMaster(SQLCore):
    async def find_payment(self, hash_id):
        res = await self.aexecute('SELECT id, chat_id, url, status, inline FROM irobot.payments WHERE hash=%s', hash_id)
        return res[0] if res else [None for _ in range(5)]

    async def upd_payment_status(self, hash_id, status):
        await self.aexecute('UPDATE irobot.payments SET status= %s WHERE hash=%s', status, hash_id)


if __name__ == '__main__':
    import asyncio

    async def main():
        sql = SQLMaster()
        res = await sql.find_payment('')
        print(res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
