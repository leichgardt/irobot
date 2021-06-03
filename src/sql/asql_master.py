try:
    from .asql_core import SQLCore
except ImportError:
    from src.sql.asql_core import SQLCore

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

    async def get_sub(self, chat_id):
        data = 'mailing, notify'
        res = await self.execute(f'SELECT {data} FROM irobot.subs WHERE subscribed=true AND chat_id=%s', chat_id)
        return res[0] if res else res

    async def get_subs(self):
        return await self.execute(f'SELECT chat_id, mailing, notify FROM irobot.subs WHERE subscribed=true')

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

    async def add_payment(self, hash_id: str, chat_id: int, url: str, agrm: str, amount: float):
        await self.execute('INSERT INTO irobot.payments(hash, chat_id, url, agrm, amount) '
                           'VALUES (%s, %s, %s, %s, %s)', hash_id, chat_id, url, agrm, amount)

    async def upd_payment(self, hash_id, **kwargs):
        upd = ', '.join([f'{key}= %s' for key in kwargs.keys()])
        await self.execute(f'UPDATE irobot.payments SET {upd}, datetime=now() WHERE hash=%s', *kwargs.values(), hash_id)

    async def cancel_payment(self, chat_id, inline):
        await self.execute('UPDATE irobot.payments SET status= %s WHERE chat_id=%s AND inline=%s',
                           'canceled', chat_id, inline)

    async def find_payment(self, hash_id):
        res = await self.execute('SELECT id, chat_id, url, status, inline, agrm, amount FROM irobot.payments '
                                 'WHERE hash=%s', hash_id)
        return res[0] if res else res

    async def find_processing_payments(self):
        return await self.execute('SELECT id, hash, chat_id, datetime, agrm, amount, notified FROM irobot.payments '
                                  'WHERE status=%s OR status=%s', 'processing', 'success')

    async def find_payments_by_record_id(self, record_id):
        return await self.execute('SELECT id FROM irobot.payments WHERE record_id=%s', record_id)


sql = SQLMaster()
