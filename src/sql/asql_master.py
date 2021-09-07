from src.sql.asql_core import SQLCore


class SQLMaster(SQLCore):
    async def get_sub(self, chat_id):
        data = 'mailing'
        res = await self.execute(f'SELECT {data} FROM irobot.subs WHERE subscribed=true AND chat_id=%s', chat_id)
        return res[0] if res else []

    async def get_subs(self, mailing=False):
        flt = 'AND mailing=true' if mailing else ''
        return await self.execute(f'SELECT chat_id, mailing FROM irobot.subs WHERE subscribed=true {flt}')

    async def add_chat(self, chat_id, msg_id, text, parse_mode=None, hash_line=None, userdata=None):
        res = await self.execute('SELECT chat_id FROM irobot.subs WHERE chat_id=%s', chat_id)
        payload = msg_id, text, parse_mode, hash_line, userdata
        if not res:
            await self.execute('INSERT INTO irobot.subs(chat_id, inline_msg_id, inline_text, inline_parse_mode, hash, '
                               'userdata) VALUES (%s, %s, %s, %s, %s, %s)', chat_id, *payload)
        else:
            await self.execute('UPDATE irobot.subs SET inline_msg_id= %s, inline_text= %s, inline_parse_mode= %s, '
                               'hash= %s, userdata= %s WHERE chat_id=%s', *payload, chat_id)

    async def upd_hash(self, chat_id, hash_code):
        await self.execute('UPDATE irobot.subs SET hash= %s WHERE chat_id=%s', hash_code, chat_id)

    async def find_chat_by_hash(self, hash_code):
        res = await self.execute('SELECT chat_id FROM irobot.subs WHERE hash=%s', hash_code)
        return res[0][0] if res else 0

    async def subscribe(self, chat_id):
        await self.execute('UPDATE irobot.subs SET subscribed=true WHERE chat_id=%s', chat_id)

    async def unsubscribe(self, chat_id):
        await self.execute('UPDATE irobot.subs SET subscribed=false WHERE chat_id=%s', chat_id)

    async def switch_sub(self, chat_id, field):
        status = await self.execute(f'SELECT {field} FROM irobot.subs WHERE chat_id=%s', chat_id)
        status = not status[0][0]
        await self.execute(f'UPDATE irobot.subs SET {field} = %s WHERE chat_id=%s', status, chat_id)

    async def get_accounts(self, chat_id):
        res = await self.execute('SELECT login FROM irobot.accounts WHERE chat_id=%s AND active=true', chat_id)
        return [acc[0] for acc in res] if res else []

    async def add_account(self, chat_id, login):
        res = await self.execute('SELECT active FROM irobot.accounts WHERE chat_id=%s AND login=%s AND active=false',
                                 chat_id, login)
        if res:
            await self.execute('UPDATE irobot.accounts SET active=true WHERE chat_id=%s AND login=%s', chat_id, login)
        else:
            await self.execute('INSERT INTO irobot.accounts (chat_id, login) VALUES (%s, %s)', chat_id, login)

    async def deactivate_account(self, chat_id: int, account: str = None):
        if account:
            await self.execute('UPDATE irobot.accounts SET active=false, update_datetime=now() '
                               'WHERE chat_id=%s AND login=%s', chat_id, account)
        else:
            await self.execute('UPDATE irobot.accounts SET active=false, update_datetime=now() WHERE chat_id=%s',
                               chat_id)

    async def get_inline(self, chat_id):
        res = await self.execute('SELECT inline_msg_id, inline_text, inline_parse_mode FROM irobot.subs '
                                 'WHERE chat_id=%s', chat_id)
        return res[0] if res else (None, None, None)

    async def upd_inline(self, chat_id: int, inline: int, text: str, parse_mode: str = None):
        await self.execute('UPDATE irobot.subs SET inline_msg_id= %s, inline_text= %s, inline_parse_mode= %s '
                           'WHERE chat_id=%s', inline, text, parse_mode, chat_id)

    async def add_review(self, chat_id, rating, comment):
        await self.execute('INSERT INTO irobot.reviews(chat_id, rating, comment) VALUES (%s, %s, %s)',
                           chat_id, rating, comment)

    async def add_payment(self, hash_code: str, chat_id: int, agrm: str, amount: float, inline: int = None):
        await self.execute('INSERT INTO irobot.payments(hash, chat_id, agrm, amount, inline) '
                           'VALUES (%s, %s, %s, %s, %s)', hash_code, chat_id, agrm, amount, inline)

    async def upd_payment(self, hash_code, **kwargs):
        upd = ', '.join([f'{key}= %s' for key in kwargs.keys()])
        await self.execute(f'UPDATE irobot.payments SET {upd}, update_datetime=now() WHERE hash=%s', *kwargs.values(), hash_code)

    async def cancel_payment(self, chat_id, inline):
        await self.execute('UPDATE irobot.payments SET status= %s WHERE chat_id=%s AND inline=%s',
                           'canceled', chat_id, inline)

    async def find_payment(self, hash_code):
        res = await self.execute('SELECT id, chat_id, status, inline, agrm, amount FROM irobot.payments '
                                 'WHERE hash=%s', hash_code, as_dict=True)
        return res[0] if res else []

    async def find_processing_payments(self):
        return await self.execute('SELECT id, hash, chat_id, status, update_datetime, agrm, amount, inline, receipt '
                                  'FROM irobot.payments WHERE status=ANY(%s)', ['processing', 'error'], as_dict=True)

    async def cancel_old_new_payments(self):
        return await self.execute('UPDATE irobot.payments SET status= %s WHERE status=%s AND '
                                  'current_date - datetime > interval \'1 day\'', 'canceled', 'new')

    async def find_payments_by_record_id(self, record_id):
        return await self.execute('SELECT id FROM irobot.payments WHERE record_id=%s', record_id)

    async def get_feedback(self, status, interval):
        """
        селект фидбеков у которых либо нету upd_dt и СОЗДАНЫ они более interval времени,
        либо у них есть upd_dt и они ОБНОВЛЕНЫ более interval времени
        """
        return await self.execute(
            'SELECT id, task_id, chat_id FROM irobot.feedback WHERE '
            '(feedback.update_datetime IS null AND status=%(status)s AND now() - datetime > interval %(interval)s) OR '
            '(feedback.update_datetime IS NOT null AND status=%(status)s AND now() - update_datetime > '
            'interval %(interval)s) ORDER BY id', {'status': status, 'interval': interval})

    async def upd_feedback(self, fb_id, **kwargs):
        upd = ', '.join([f'{key}= %s' for key in kwargs.keys()])
        await self.execute(f'UPDATE irobot.feedback SET update_datetime=now(), {upd} WHERE id=%s',
                           *kwargs.values(), fb_id)

    async def find_feedback_id(self, task_id, status):
        res = await self.execute('SELECT id FROM irobot.feedback WHERE task_id=%s AND status=%s ORDER BY id DESC '
                                 'LIMIT 1', task_id, status)
        return res[0][0] if res else 0

    async def get_sub_agrms(self):
        return await self.execute('SELECT s.chat_id, a.login, s.mailing FROM irobot.subs s JOIN irobot.accounts a '
                                  'ON s.chat_id=a.chat_id WHERE s.subscribed=true ORDER BY s.chat_id')

    async def get_mailings(self):
        return await self.execute('SELECT id, datetime, type, text FROM irobot.mailing ORDER BY id DESC LIMIT 10')

    async def add_mailing(self, mail_type, text):
        return await self.execute('INSERT INTO irobot.mailing (type, text) VALUES (%s, %s) RETURNING id', mail_type, text)

    async def get_new_mailings(self):
        return await self.execute("SELECT id, type, text FROM irobot.mailing WHERE status='new'")

    async def upd_mailing_status(self, mail_id, status):
        return await self.execute('UPDATE irobot.mailing SET status= %s WHERE id=%s', status, mail_id)

    async def add_pid(self, pid: int):
        await self.execute('INSERT INTO irobot.pids(pid) VALUES (%s)', pid, log_faults=False)

    async def get_pid_list(self):
        return await self.execute('SELECT pid, tasks FROM irobot.pids')

    async def del_pid_list(self):
        await self.execute('DELETE FROM irobot.pids')

    async def find_uncompleted_task(self, task_id):
        return await self.execute('SELECT id FROM cardinalis.tasks WHERE task_id=%s AND NOT status '
                                  'ORDER BY id DESC LIMIT 1', task_id)

    async def finish_feedback_task(self, task_id):
        await self.execute('UPDATE cardinalis.tasks SET status=true, update_datetime=now() '
                           'WHERE status=false AND task_id=%s', task_id)


sql = SQLMaster()

if __name__ == '__main__':
    import asyncio
    from src.utils import config

    async def main():
        res = await sql.get_accounts(config['irobot']['me'])
        print(res)

    asyncio.run(main())
