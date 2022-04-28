from datetime import datetime

from src.bot.utils import support as support_utils
from src.modules import sql
from src.web.utils import telegram_api


async def get_support_list():
    """ Получить список чатов, находящихся в поддержке, и данных о них """
    chats = await sql.execute(
        '''
        SELECT c.chat_id, c.closed, o.oper_id, o.full_name as oper_name, s.first_name, s.photo, MAX(m.datetime) as dt,
        m.read, m2.min_message_id
            FROM irobot.support c
            LEFT JOIN irobot.support cc
                ON c.chat_id = cc.chat_id AND c.opened < cc.opened
            LEFT JOIN irobot.operators o
                ON c.oper_id = o.oper_id
            LEFT JOIN irobot.subs s
                ON c.chat_id = s.chat_id
            JOIN (
                SELECT m.chat_id, MAX(m.datetime) as datetime, m.read 
                    FROM irobot.support_messages m
                    LEFT JOIN irobot.support_messages mm
                        ON m.chat_id = mm.chat_id AND m.datetime < mm.datetime
                    WHERE mm.chat_id IS null
                    GROUP BY m.chat_id, m.read
            ) m
                ON c.chat_id = m.chat_id
            JOIN (
                SELECT chat_id, MIN(message_id) as min_message_id
                    FROM irobot.support_messages
                    GROUP BY chat_id
            ) m2
                ON c.chat_id = m2.chat_id
        WHERE cc.chat_id IS NULL
        GROUP BY c.chat_id, c.closed, o.oper_id, oper_name, s.first_name, s.photo, m.read, m2.min_message_id
        ORDER BY dt DESC''',
        as_dict=True
    )
    for chat in chats:
        sql.split_datetime(chat, 'dt')
        chat.update({'support_mode': False if chat['closed'] else True})
        chat.pop('closed')
    return {i: {key: value.strftime('%H:%M:%S %d.%m.%Y') if isinstance(value, datetime) else value
                for key, value in chat.items()}
            for i, chat in enumerate(chats)} if chats else {}


async def get_accounts_and_chats():
    chats = await get_support_list()
    accounts = await get_chat_accounts_in_support_need()
    for chat in chats.values():
        chat['accounts'] = accounts[chat['chat_id']]
    return chats


async def get_new_support_messages():
    res = await sql.execute(
        'SELECT m.chat_id, m.message_id, m.datetime, o.oper_id, o.full_name as oper_name, m.content_type, m.content '
        'FROM irobot.support_messages m LEFT JOIN irobot.operators o ON m.from_oper = o.oper_id '
        'WHERE status=%s ORDER BY datetime',
        'new', as_dict=True
    )
    for msg in res:
        sql.split_datetime(msg)
    return res


async def get_messages_from_range(chat_id: int, end_message_id: int = 0):
    flt = '' if not end_message_id else f'AND message_id < {end_message_id}'
    return await sql.execute(
        f'SELECT m.message_id, m.datetime, m.from_oper AS oper_id, o.full_name AS oper_name, m.content_type, m.content '
        f'FROM irobot.support_messages m LEFT JOIN irobot.operators o ON m.from_oper=o.oper_id '
        f'WHERE m.chat_id=%s {flt} ORDER BY m.datetime DESC LIMIT 10', chat_id, as_dict=True
    )


async def get_messages_from_id_list(chat_id: int, id_list: list):
    return await sql.execute(
        f'SELECT m.message_id, m.datetime, m.from_oper AS oper_id, o.full_name AS oper_name, m.content_type, m.content '
        f'FROM irobot.support_messages m LEFT JOIN irobot.operators o ON m.from_oper=o.oper_id '
        f'WHERE m.chat_id=%s AND m.message_id=any (%s) ORDER BY m.datetime DESC LIMIT 10', chat_id, id_list,
        as_dict=True
    )


async def get_chat_messages(chat_id: int, end_message_id: int = 0, id_list: list = None):
    if not id_list:
        messages = await get_messages_from_range(chat_id, end_message_id)
    else:
        messages = await get_messages_from_id_list(chat_id, id_list)
    for msg in messages:
        sql.split_datetime(msg)
    id_list = [msg['message_id'] for msg in messages]
    ts_list = {msg['timestamp']: msg['message_id'] for msg in messages}
    messages = {msg['message_id']: msg for msg in messages}
    return {
        'messages': messages,
        'chat_id': chat_id,
        'id_list': id_list,
        'ts_list': ts_list,
        'first_message_id': id_list[-1]
    }


async def send_oper_message(data, oper_id, oper_name, **kwargs):
    msg = await telegram_api.send_message(data['chat_id'], data['text'], **kwargs)
    if msg and msg.message_id > 0:
        await set_chat_status_read(data['chat_id'])
        msg_date = await support_utils.add_support_message_to_db(
            data['chat_id'], msg.message_id, 'text', {'text': data['text']}, oper_id, read=True, status=None
        )
        msg_date = msg_date or datetime.now()
        date, time, timestamp = sql.split_datetime(msg_date)
        return {
            'chat_id': data['chat_id'],
            'message_id': msg.message_id,
            'date': date,
            'time': time,
            'timestamp': timestamp,
            'oper_id': oper_id,
            'oper_name': oper_name,
            'content_type': 'text',
            'content': {'text': data['text']}
        }


async def take_chat(chat_id, oper_id):
    support_id = await get_live_support_id(chat_id)
    await set_oper_to_support(support_id, oper_id)
    await add_support_operation(support_id, oper_id, 'take')


async def drop_chat(chat_id, oper_id):
    support_id = await get_live_support_id(chat_id)
    await set_oper_to_support(support_id, None)
    await add_support_operation(support_id, oper_id, 'drop')


async def finish_support(chat_id, oper_id):
    support_id = await get_live_support_id(chat_id)
    await set_oper_to_support(support_id, None)
    await add_support_operation(support_id, oper_id, 'close')
    await close_support_line(chat_id)
    await set_chat_status_read(chat_id)
    await support_utils.add_system_support_message(chat_id, 0, 'Поддержка закрыта')
    # todo add review


async def get_live_support_id(chat_id):
    res = await sql.execute(
        'SELECT support_id FROM irobot.support WHERE chat_id=%(chat_id)s AND (closed IS null OR '
        'closed=(SELECT MAX(closed) FROM irobot.support WHERE chat_id=%(chat_id)s)) ORDER BY support_id DESC',
        {'chat_id': chat_id}, as_dict=True, fetch_one=True
    )
    return res['support_id'] if res else None


async def set_oper_to_support(support_id, oper_id):
    await sql.execute('UPDATE irobot.support SET oper_id= %s WHERE support_id=%s', oper_id, support_id)


async def add_support_operation(support_id, oper_id, operation):
    await sql.execute('INSERT INTO irobot.support_oper_history (support_id, oper_id, operation) VALUES (%s, %s, %s)',
                      support_id, oper_id, operation)


async def close_support_line(chat_id):
    await sql.execute('UPDATE irobot.support SET closed=now() WHERE chat_id=%s AND closed IS null', chat_id)


async def get_chat_accounts_in_support_need():
    subs = await sql.execute(
        'SELECT chat_id, login FROM irobot.accounts WHERE active=true '
        'AND chat_id IN (SELECT DISTINCT chat_id FROM irobot.support_messages)', as_dict=True
    )
    accounts = {}
    for sub in subs:
        if sub['chat_id'] not in accounts:
            accounts[sub['chat_id']] = [sub['login']]
        else:
            accounts[sub['chat_id']].append(sub['login'])
    return accounts


async def set_chat_status_read(chat_id):
    await sql.execute('UPDATE irobot.support_messages SET read=true WHERE chat_id=%s', chat_id)


async def find_missing_messages(chat_id, message_id_list):
    message_id_list = [int(i) for i in message_id_list]
    messages = await get_missed_messages_between_min_max_id_list(chat_id, message_id_list)
    if messages:
        for message in messages:
            sql.split_datetime(message)
        messages = {message['message_id']: message for message in messages}
        return messages


async def get_missed_messages_between_min_max_id_list(chat_id, message_id_list):
    return await sql.execute(
        '''
        SELECT m.chat_id, m.message_id, m.datetime, m.from_oper as oper_id, o.full_name as oper_name, m.content_type,
        m.content, m.read
            FROM irobot.support_messages m 
            LEFT JOIN irobot.operators o 
                ON m.from_oper = o.oper_id
        WHERE m.message_id != all(%(list)s)
            AND m.chat_id = %(id)s
            AND (
                m.datetime > (
                    SELECT MAX(datetime) FROM irobot.support_messages
                        WHERE chat_id=%(id)s AND message_id=any(%(list)s))
                OR (
                    m.datetime > (
                        SELECT MIN(datetime) FROM irobot.support_messages
                            WHERE chat_id=%(id)s AND message_id=any(%(list)s))
                    AND m.datetime < (
                        SELECT MAX(datetime) FROM irobot.support_messages
                            WHERE chat_id=%(id)s AND message_id=any(%(list)s))
                )
            )
        ORDER BY m.datetime DESC''',
        {'id': chat_id, 'list': message_id_list}, as_dict=True
    )
