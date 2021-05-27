try:
    from .asql_core import SQLCore
except ImportError:
    from asql_core import SQLCore

import ujson


class SQLMaster(SQLCore):
    async def get_fsm(self, chat_id):
        data = 'id, operation, stage, data'
        res = await self.execute(f'SELECT {data} FROM irobot.fsm WHERE chat_id=%s AND stage>0 '
                                 f'ORDER BY id DESC LIMIT 1', chat_id)
        return res[0] if res else (None for _ in data.split(', '))

    async def add_fsm(self, chat_id, operation):
        res = await self.execute('INSERT INTO irobot.fsm(chat_id, operation, stage, data) VALUES (%s, %s, 1, %s) '
                                 'RETURNING id', chat_id, operation, {})
        return res[0][0] if res else None

    async def upd_fsm(self, fsm_id: int, stage: int, data: dict):
        await self.execute('UPDATE irobot.fsm SET stage= %s WHERE id=%s', stage, ujson.dumps(data), fsm_id)

    async def get_sub(self, chat_id=None):
        data = 'mailing, notify'
        if chat_id:
            res = await self.execute(f'SELECT {data} FROM irobot.subs WHERE subscribed=true AND chat_id=%s', chat_id)
        else:
            res = await self.execute(f'SELECT {data} FROM irobot.subs WHERE subscribed=true')
        return res[0] if res and chat_id is not None else res

    async def get_subs(self):
        return await self.get_sub(chat_id=None)

    async def get_chat(self, chat_id):
        res = await self.execute('SELECT chat_id, subscribed FROM irobot.subs WHERE chat_id=%s', chat_id)
        return res[0] if res else (None, None)

    async def add_chat(self, chat_id, msg_id, text, parse_mode=None):
        res = await self.execute('SELECT chat_id FROM irobot.subs WHERE chat_id=%s', chat_id)
        if not res:
            await self.execute('INSERT INTO irobot.subs(chat_id, inline_msg_id, inline_text, inline_parse_mode) VALUES '
                               '(%s, %s, %s, %s)', chat_id, msg_id, text, parse_mode)
        else:
            await self.upd_inline(chat_id, msg_id, text, parse_mode=parse_mode)

    async def subscribe(self, chat_id):
        await self.execute('UPDATE irobot.subs SET subscribed=true WHERE chat_id=%s', chat_id)

    async def unsubscribe(self, chat_id):
        await self.execute('UPDATE irobot.subs SET subscribed=false WHERE chat_id=%s', chat_id)

    async def switch_sub(self, chat_id, field):
        status = await self.execute(f'SELECT {field} FROM irobot.subs WHERE chat_id=%s', chat_id)
        status = not status[0][0]
        await self.execute(f'UPDATE irobot.subs SET {field} = %s WHERE chat_id=%s', status, chat_id)

    async def get_agrms(self, chat_id):
        res = await self.execute('SELECT agrm FROM irobot.agrms WHERE chat_id=%s', chat_id)
        return [line[0] for line in res] if res else []

    async def get_agrm_id(self, chat_id, agrm):
        res = await self.execute('SELECT agrm_id FROM irobot.agrms WHERE chat_id=%s and agrm=%s', chat_id, agrm)
        return res[0][0] if res else []

    async def add_agrm(self, chat_id, agrm, agrm_id):
        await self.execute('INSERT INTO irobot.agrms(chat_id, agrm, agrm_id) VALUES (%s, %s, %s)',
                           chat_id, agrm, agrm_id)

    async def del_agrm(self, chat_id, agrm):
        await self.execute('DELETE FROM irobot.agrms WHERE chat_id=%s AND agrm=%s', chat_id, agrm)

    async def get_inline(self, chat_id):
        res = await self.execute('SELECT inline_msg_id, inline_text, inline_parse_mode FROM irobot.subs '
                                 'WHERE chat_id=%s', chat_id)
        return res[0] if res else (None, None, {})

    async def upd_inline(self, chat_id: int, inline: int, text: str, parse_mode: str = None):
        await self.execute('UPDATE irobot.subs SET inline_msg_id= %s, inline_text= %s, inline_parse_mode= %s '
                           'WHERE chat_id=%s', inline, text, parse_mode, chat_id)

    async def add_review(self, chat_id, rating, comment):
        await self.execute('INSERT INTO irobot.reviews(chat_id, rating, comment) VALUES (%s, %s, %s)',
                           chat_id, rating, comment)

    async def get_payment(self, hash_id):
        res = await self.execute('SELECT chat_id, url, status, inline FROM irobot.payments WHERE hash=%s', hash_id)
        return res[0] if res else None

    async def add_payment(self, hash_id, chat_id, url):
        await self.execute('INSERT INTO irobot.payments(hash, chat_id, url) VALUES (%s, %s, %s)', hash_id, chat_id, url)

    async def upd_payment(self, hash_id, inline):
        await self.execute('UPDATE irobot.payments SET inline= %s WHERE hash=%s', inline, hash_id)

    async def cancel_payment(self, chat_id, inline):
        await self.execute('UPDATE irobot.payments SET status= %s WHERE chat_id=%s AND inline=%s',
                           'canceled', chat_id, inline)


sql = SQLMaster()

if __name__ == '__main__':
    import asyncio

    async def main():
        res = await sql.get_payment('')
        print(res)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
