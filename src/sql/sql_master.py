try:
    from .sql_core import SQLCore
except ImportError:
    from sql_core import SQLCore


class SQLMaster(SQLCore):
    async def get_payment(self, hash_id):
        res = await self.aexecute('SELECT chat_id, url, status, inline FROM irobot.payments WHERE hash=%s', hash_id)
        return res[0] if res else None

    async def add_payment(self, hash_id, chat_id, url):
        await self.aexecute('INSERT INTO irobot.payments(hash, chat_id, url) VALUES (%s, %s, %s)', hash_id, chat_id, url)

    async def upd_payment(self, hash_id, inline):
        await self.aexecute('UPDATE irobot.payments SET inline= %s WHERE hash=%s', inline, hash_id)

    async def cancel_payment(self, chat_id, inline):
        await self.aexecute('UPDATE irobot.payments SET status="canceled" WHERE chat_id=%s AND inline=%s', chat_id, inline)


if __name__ == '__main__':
    import asyncio

    async def main():
        sql = SQLMaster()
        res = await sql.get_payment('')
        print(res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
