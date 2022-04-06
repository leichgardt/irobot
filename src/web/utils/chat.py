from src.bot.schemas import keyboards
from src.modules import sql
from src.web.utils.telegram_api import send_message


async def get_accounts_and_chats():
    chats = await sql.get_support_dialog_list()
    accounts = await get_chat_accounts_in_support_need()
    return {'chats': chats, 'accounts': accounts}


async def get_subscriber_message(chat_id, message_id):
    msg = await sql.execute(
        'select chat_id, message_id, datetime, from_oper as oper_id, content_type, content '
        'from irobot.support_messages where chat_id=%s and message_id=%s', chat_id, message_id,
        as_dict=True, fetch_one=True
    )
    if msg:
        sql.split_datetime(msg)
    return msg if msg else {}


async def get_chat_messages(chat_id, page=0):
    msgs = await sql.execute(
        'select m.message_id, m.datetime, m.from_oper as oper_id, o.full_name as oper_name, m.content_type, m.content '
        'from irobot.support_messages m left join irobot.operators o on m.from_oper=o.oper_id '
        'where m.chat_id=%s order by datetime desc', chat_id, as_dict=True
    )
    for msg in msgs:
        sql.split_datetime(msg)
    msgs.reverse()
    return msgs


async def send_oper_message(data, oper_id, oper_name, **kwargs):
    msg = await send_message(data['chat_id'], data['text'], **kwargs)
    if msg and msg.message_id > 0:
        dt = await sql.insert(
            'insert into irobot.support_messages (chat_id, message_id, from_oper, content_type, content) '
            'values (%s, %s, %s, %s, %s) returning datetime',
            data['chat_id'], msg.message_id, oper_id, 'text', {'text': data['text']}
        )
        date, time = sql.split_datetime(dt)
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
    await sql.update('irobot.support_chats', f'chat_id={chat_id}', oper_id=oper_id)


async def drop_chat(chat_id, oper_id):
    await sql.update('irobot.support_chats', f'chat_id={chat_id} and oper_id={oper_id}', oper_id=None)


async def finish_support(chat_id, oper_id, oper_name):
    # todo переделать support_chats в support (support_id, feedback) и support_operators (oper_id, datetime)
    await sql.update('irobot.support_chats', f'chat_id={chat_id}', support_mode=False, oper_id=None)
    return await send_oper_message({'chat_id': chat_id, 'text': 'Спасибо за обращение!'}, oper_id, oper_name,
                                   reply_markup=keyboards.main_menu_kb)
    # todo add review


async def get_chat_accounts_in_support_need():
    subs = await sql.execute(
        'select chat_id, login from irobot.accounts where active=true '
        'and chat_id in (select distinct chat_id from irobot.support_messages)', as_dict=True
    )
    accounts = {}
    for sub in subs:
        if sub['chat_id'] not in accounts:
            accounts[sub['chat_id']] = [sub['login']]
        else:
            accounts[sub['chat_id']].append(sub['login'])
    return accounts


async def read_chat(chat_id):
    await sql.execute('update irobot.support_chats set read=true where chat_id=%s', chat_id)
