from datetime import datetime

from src.bot.schemas import keyboards
from src.bot.utils import support
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
    return {'chats': chats, 'accounts': accounts}


async def get_subscriber_message(chat_id, message_id):
    msg = await sql.execute(
        'SELECT chat_id, message_id, datetime, from_oper AS oper_id, content_type, content '
        'FROM irobot.support_messages WHERE chat_id=%s AND message_id=%s', chat_id, message_id,
        as_dict=True, fetch_one=True
    )
    if msg:
        sql.split_datetime(msg)
    return msg if msg else {}


async def get_chat_messages(chat_id, end_message_id=0):
    flt = '' if not end_message_id else f'AND message_id < {end_message_id}'
    messages = await sql.execute(
        f'SELECT m.message_id, m.datetime, m.from_oper AS oper_id, o.full_name AS oper_name, m.content_type, m.content '
        f'FROM irobot.support_messages m LEFT JOIN irobot.operators o ON m.from_oper=o.oper_id '
        f'WHERE m.chat_id=%s {flt} ORDER BY message_id DESC LIMIT 10', chat_id, as_dict=True
    )
    for msg in messages:
        sql.split_datetime(msg)
    messages = {msg['message_id']: msg for msg in messages}
    return {'messages': messages, 'chat_id': chat_id, 'first_message_id': min(messages.keys())}


async def send_oper_message(data, oper_id, oper_name, **kwargs):
    msg = await telegram_api.send_message(data['chat_id'], data['text'], **kwargs)
    if msg and msg.message_id > 0:
        await read_chat(data['chat_id'])
        msg_date = await support.add_support_message_to_db(
            data['chat_id'], msg.message_id, 'text', {'text': data['text']}, oper_id, read=True, status=None
        )
        date, time = sql.split_datetime(msg_date if msg_date else datetime.now())
        return {
            'chat_id': data['chat_id'],
            'message_id': msg.message_id,
            'date': date,
            'time': time,
            'oper_id': oper_id,
            'oper_name': oper_name,
            'content_type': 'text',
            'content': {'text': data['text']}
        }


async def take_chat(chat_id, oper_id):
    sup = await get_live_support(chat_id)
    await set_oper_to_support(sup['support_id'], oper_id)
    await add_support_operation(sup['support_id'], oper_id, 'take')


async def drop_chat(chat_id, oper_id):
    sup = await get_live_support(chat_id)
    await set_oper_to_support(sup['support_id'], None)
    await add_support_operation(sup['support_id'], oper_id, 'drop')


async def finish_support(chat_id, oper_id, oper_name):
    sup = await get_live_support(chat_id)
    await set_oper_to_support(sup['support_id'], None)
    await add_support_operation(sup['support_id'], oper_id, 'close')
    await close_support_line(chat_id)
    return await send_oper_message({'chat_id': chat_id, 'text': 'Спасибо за обращение!'}, oper_id, oper_name,
                                   reply_markup=keyboards.main_menu_kb)
    # todo add review


async def get_live_support(chat_id):
    return await sql.execute('SELECT support_id FROM irobot.support WHERE chat_id=%(chat_id)s AND (closed IS null OR '
                             'closed=(SELECT MAX(closed) FROM irobot.support WHERE chat_id=%(chat_id)s))',
                             {'chat_id': chat_id}, as_dict=True, fetch_one=True)


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


async def read_chat(chat_id):
    await sql.execute('UPDATE irobot.support_messages SET read=true WHERE chat_id=%s', chat_id)
