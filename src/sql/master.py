from datetime import datetime

from src.parameters import PID_TABLE
from src.sql.core import SQLCore


class SQLMaster(SQLCore):
    async def get_sub(self, chat_id):
        data = 'mailing'
        res = await self.execute(f'SELECT {data} FROM irobot.subs WHERE subscribed=true AND chat_id=%s', chat_id)
        return res[0] if res else []

    async def get_subs(self, mailing=False):
        flt = 'AND mailing=true' if mailing else ''
        return await self.execute(f'SELECT chat_id, mailing FROM irobot.subs WHERE subscribed=true {flt}')

    async def add_chat(self, chat_id, msg_id, text, parse_mode=None, hash_line=None, username=None, first_name=None,
                       last_name=None):
        res = await self.execute('SELECT chat_id FROM irobot.subs WHERE chat_id=%s', chat_id)
        payload = msg_id, text, parse_mode, hash_line, username, first_name, last_name
        if not res:
            await self.execute(
                'INSERT INTO irobot.subs(chat_id, inline_msg_id, inline_text, inline_parse_mode, hash, username, '
                'first_name, last_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', chat_id, *payload)

        else:
            await self.execute(
                'UPDATE irobot.subs SET inline_msg_id= %s, inline_text= %s, inline_parse_mode= %s, hash= %s, '
                'username= %s, first_name= %s, last_name= %s WHERE chat_id=%s', *payload, chat_id
            )

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

    async def find_user_chats(self, user_id):
        res = await self.execute('SELECT a.chat_id FROM irobot.accounts a JOIN irobot.subs s ON s.chat_id=a.chat_id '
                                 'WHERE a.user_id=%s AND a.active=true AND s.subscribed=true', user_id)
        return [line[0] for line in res] if res else []

    async def get_accounts(self, chat_id):
        res = await self.execute('SELECT login FROM irobot.accounts WHERE chat_id=%s AND active=true', chat_id)
        return [acc[0] for acc in res] if res else []

    async def add_account(self, chat_id, login, user_id):
        res = await self.execute('SELECT active FROM irobot.accounts WHERE chat_id=%s AND login=%s AND active=false',
                                 chat_id, login)
        if res:
            await self.execute('UPDATE irobot.accounts SET active=true WHERE chat_id=%s AND login=%s', chat_id, login)
        else:
            await self.execute('INSERT INTO irobot.accounts (chat_id, login, user_id) VALUES (%s, %s, %s)',
                               chat_id, login, user_id)

    async def deactivate_account(self, chat_id: int, account: str = None):
        if account:
            await self.execute('UPDATE irobot.accounts SET active=false, update_datetime=now() '
                               'WHERE chat_id=%s AND login=%s', chat_id, account)
        else:
            await self.execute('UPDATE irobot.accounts SET active=false, update_datetime=now() WHERE chat_id=%s',
                               chat_id)

    async def get_inline_message(self, chat_id):
        res = await self.execute('SELECT inline_msg_id, inline_text, inline_parse_mode FROM irobot.subs '
                                 'WHERE chat_id=%s', chat_id)
        return res[0] if res else (0, '', None)

    async def upd_inline_message(self, chat_id: int, inline: int, text: str, parse_mode: str = None):
        await self.execute('UPDATE irobot.subs SET inline_msg_id= %s, inline_text= %s, inline_parse_mode= %s '
                           'WHERE chat_id=%s', inline, text, parse_mode, chat_id)

    async def add_review(self, chat_id, rating, comment):
        await self.execute('INSERT INTO irobot.reviews(chat_id, rating, comment) VALUES (%s, %s, %s)',
                           chat_id, rating, comment)

    async def add_payment(self, hash_code: str, chat_id: int, agrm: str, amount: float, inline: int = None,
                          balance: int = None, status: str = None):
        res = await self.execute('INSERT INTO irobot.payments(hash, chat_id, agrm, amount, inline, balance, status) '
                                 'VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id',
                                 hash_code, chat_id, agrm, amount, inline, balance, status)
        return res[0][0] if res else 0

    async def upd_payment(self, hash_code, **kwargs):
        upd = ', '.join([f'{key}= %s' for key in kwargs.keys()])
        await self.execute(f'UPDATE irobot.payments SET {upd}, update_datetime=now() WHERE hash=%s', *kwargs.values(), hash_code)

    async def find_payment(self, hash_code):
        res = await self.execute('SELECT id, chat_id, status, inline, agrm, amount, url, receipt FROM irobot.payments '
                                 'WHERE hash=%s', hash_code, as_dict=True)
        return res[0] if res else []

    async def find_processing_payments(self):
        return await self.execute(
            'SELECT * FROM irobot.payments WHERE status=\'error\' OR'
            '(status=\'success\' AND current_date - update_datetime > interval \'5 minute\') OR '
            '(status=\'processing\' AND current_date - update_datetime > interval \'1 hour\')',
            as_dict=True
        )

    async def cancel_old_new_payments(self):
        return await self.execute('UPDATE irobot.payments SET status= %s WHERE status=%s AND '
                                  'current_date - datetime > interval \'1 day\'', 'canceled', 'new')

    async def find_payments_by_record_id(self, record_id):
        return await self.execute('SELECT id FROM irobot.payments WHERE record_id=%s', record_id)

    async def add_feedback(self, chat_id, type_, object_=None, rating=None, comment=None, status='new'):
        return await self.insert('INSERT INTO irobot.feedback (chat_id, type, object, rating, comment, status) VALUES ('
                                 '%s, %s, %s, %s, %s, %s) RETURNING id',
                                 chat_id, type_, object_, rating, comment, status)

    async def get_feedback(self, interval='1 hours'):
        """
        Загрузка feedback пользователей со статусом "sending" или "new", которые созданы более часа назад (по умолчанию)

        :param interval: Интервал времени для feedback со статусом "new"
        :return Список feedbacks, которые состоят из [id, chat_id, task_id, rating, comment]
        """
        return await self.execute(
            "SELECT id, chat_id, object, rating, comment FROM irobot.feedback WHERE type='feedback' AND "
            "(status='sending' OR (status='new' AND update_datetime IS null AND now() - datetime > interval %s) OR "
            "(status='new' AND update_datetime IS NOT null AND now() - update_datetime > interval %s)) ORDER BY id DESC"
            , interval, interval
        )

    async def upd_feedback(self, fb_id, **kwargs):
        upd = ', '.join([f'{key}= %s' for key in kwargs.keys()])
        await self.execute(f'UPDATE irobot.feedback SET update_datetime=now(), {upd} WHERE id=%s',
                           *kwargs.values(), fb_id)

    async def get_sub_accounts(self):
        return await self.execute('SELECT s.chat_id, a.login, s.mailing FROM irobot.subs s JOIN irobot.accounts a '
                                  'ON s.chat_id=a.chat_id WHERE s.subscribed=true AND a.active=true ORDER BY s.chat_id')

    async def get_mailings(self):
        return await self.execute('SELECT id, datetime, status, type, targets, text FROM irobot.mailing '
                                  'ORDER BY id DESC LIMIT 10', as_dict=True)

    async def add_mailing(self, mail_type: str, text: str, targets: list = None, parse_mode: str = None):
        res = await self.execute('INSERT INTO irobot.mailing (type, text, targets, parse_mode) VALUES (%s, %s, %s, %s) '
                                 'RETURNING id', mail_type, text, targets, parse_mode)
        return res[0][0] if res else 0

    async def upd_mailing_status(self, mail_id, status):
        return await self.execute('UPDATE irobot.mailing SET status= %s WHERE id=%s', status, mail_id)

    async def add_pid(self, pid: int):
        await self.execute(f'INSERT INTO irobot.{PID_TABLE}(pid) VALUES (%s)', pid, log_faults=False)

    async def get_pid_list(self):
        return await self.execute(f'SELECT pid, tasks FROM irobot.{PID_TABLE}')

    async def del_pid_list(self):
        await self.execute(f'DELETE FROM irobot.{PID_TABLE}')

    async def find_uncompleted_task(self, task_id):
        return await self.execute('SELECT id FROM cardinalis.tasks WHERE task_id=%s AND NOT status '
                                  'ORDER BY id DESC LIMIT 1', task_id)

    async def finish_feedback_task(self, task_id):
        await self.execute('UPDATE cardinalis.tasks SET status=true, update_datetime=now() '
                           'WHERE status=false AND task_id=%s', task_id)

    async def add_support_message(self, chat_id, message_id, writer, message_type, message_data):
        await self.insert('INSERT INTO irobot.support_dialogs (chat_id, message_id, writer, type, data, datetime) '
                          'VALUES (%s, %s, %s, %s, %s, %s)', chat_id, message_id, writer, message_type, message_data, datetime.now())


sql = SQLMaster()

if __name__ == '__main__':
    import asyncio
    from src.parameters import TEST_CHAT_ID

    async def main():
        res = await sql.get_accounts(TEST_CHAT_ID)
        print(res)

    asyncio.run(main())
